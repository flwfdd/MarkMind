"""Database connection and operations - Optimized for SurrealDB"""

from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from surrealdb import (
    BlockingHttpSurrealConnection,
    BlockingWsSurrealConnection,
    RecordID,
    Surreal,
    Value,
)

# Type alias for SurrealDB connection
SurrealConnection = BlockingWsSurrealConnection | BlockingHttpSurrealConnection


class Database:
    """Database connection manager"""

    def __init__(self):
        self.conn: Optional[SurrealConnection] = None

    def connect(self):
        """Connect to SurrealDB"""
        if self.conn is None:
            self.conn = Surreal(settings.surrealdb_url)
            self.conn.signin(
                {
                    "username": settings.surrealdb_username,
                    "password": settings.surrealdb_password,
                }
            )
            self.conn.use(settings.surrealdb_namespace, settings.surrealdb_database)

    def disconnect(self):
        """Disconnect from SurrealDB"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_schema(self):
        """Initialize database schema with tables and indexes"""
        self.connect()
        if self.conn is None:
            return

        # Define doc table (no embedding, search via chunks)
        self.conn.query(
            """
            DEFINE TABLE IF NOT EXISTS doc SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS title ON TABLE doc TYPE string;
            DEFINE FIELD IF NOT EXISTS summary ON TABLE doc TYPE string;
            DEFINE FIELD IF NOT EXISTS content ON TABLE doc TYPE string;
            DEFINE FIELD IF NOT EXISTS type ON TABLE doc TYPE string ASSERT $value IN ['pdf', 'md', 'xhs', 'text'];
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE doc TYPE datetime DEFAULT time::now();
            DEFINE FIELD IF NOT EXISTS url ON TABLE doc TYPE option<string>;
        """
        )

        # Define concept table
        self.conn.query(
            """
            DEFINE TABLE IF NOT EXISTS concept SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS name ON TABLE concept TYPE string;
            DEFINE FIELD IF NOT EXISTS desc ON TABLE concept TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE concept TYPE array<float, 1024>;
            DEFINE INDEX IF NOT EXISTS concept_embedding ON TABLE concept FIELDS embedding HNSW DIMENSION 1024 DIST COSINE TYPE F32;
        """
        )

        # Define chunk table
        self.conn.query(
            """
            DEFINE TABLE IF NOT EXISTS chunk SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS text ON TABLE chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE chunk TYPE array<float, 1024>;
            DEFINE FIELD IF NOT EXISTS source ON TABLE chunk TYPE record<doc>;
            DEFINE INDEX IF NOT EXISTS chunk_embedding ON TABLE chunk FIELDS embedding HNSW DIMENSION 1024 DIST COSINE TYPE F32;
        """
        )

        # Define mentions edge
        self.conn.query(
            """
            DEFINE TABLE IF NOT EXISTS mentions SCHEMAFULL TYPE RELATION IN doc OUT concept;
            DEFINE FIELD IF NOT EXISTS desc ON TABLE mentions TYPE option<string>;
        """
        )

        # Define related edge
        self.conn.query(
            """
            DEFINE TABLE IF NOT EXISTS related SCHEMAFULL TYPE RELATION IN concept OUT concept;
            DEFINE FIELD IF NOT EXISTS desc ON TABLE related TYPE option<string>;
        """
        )

    def create_doc(
        self,
        title: str,
        summary: str,
        content: str,
        doc_type: str,
        url: Optional[str] = None,
    ) -> str:
        """Create a new document (no embedding, search via chunks)"""
        if self.conn is None:
            return ""
        result = self.conn.query(  # type: ignore
            """
            CREATE doc CONTENT {
                title: $title,
                summary: $summary,
                content: $content,
                type: $type,
                url: $url,
                created_at: $created_at
            }
            """,
            {
                "title": title,
                "summary": summary,
                "content": content,
                "type": doc_type,
                "url": url,
                "created_at": datetime.now(timezone.utc),  # type: ignore
            },
        )
        # conn.query returns a list with result list
        if isinstance(result, list) and len(result) > 0:
            items = result[0] if isinstance(result[0], list) else result
            if len(items) > 0 and isinstance(items[0], dict):
                return str(items[0]["id"])  # type: ignore
        return ""

    def create_chunk(self, text: str, embedding: list[float], source_id: str) -> str:
        """Create a new chunk"""
        if self.conn is None:
            return ""

        # Parse source_id to get table and id parts
        # source_id format: "table:id" or just "id"
        if ":" in source_id:
            table, record_id = source_id.split(":", 1)
        else:
            table, record_id = "doc", source_id

        result = self.conn.query(  # type: ignore
            f"""
            CREATE chunk CONTENT {{
                text: $text,
                embedding: $embedding,
                source: type::thing($table, $record_id)
            }}
            """,
            {
                "text": text,
                "embedding": embedding,  # type: ignore
                "table": table,
                "record_id": record_id,
            },
        )
        # conn.query returns a list with result list
        if isinstance(result, list) and len(result) > 0:
            items = result[0] if isinstance(result[0], list) else result
            if len(items) > 0 and isinstance(items[0], dict):
                return str(items[0]["id"])  # type: ignore
        return ""

    def create_concept(self, name: str, desc: str, embedding: list[float]) -> str:
        """Create or get a concept by name.

        Concepts now have an explicit `name` field and use randomly-assigned
        record IDs (e.g., `concept:xyz`). If a concept with the same `name`
        already exists, return its ID, otherwise create a new record and
        return the assigned ID.
        """
        if self.conn is None:
            return ""

        # Try to find an existing concept with this name
        try:
            result = self.conn.query(
                "SELECT * FROM concept WHERE name = $name",
                {"name": name},
            )
        except Exception:
            result = None

        # Normalize result to rows list (support different client shapes)
        rows: list = []
        if isinstance(result, list) and len(result) > 0:
            first = result[0]
            if (
                isinstance(first, dict)
                and "result" in first
                and isinstance(first["result"], list)
            ):
                rows = first["result"]
            elif all(isinstance(item, dict) for item in result):
                rows = result  # type: ignore
            elif isinstance(first, list):
                rows = first  # type: ignore

        if rows:
            # Return the id of the first matching concept
            concept = rows[0]
            return str(concept.get("id"))

        # Create new concept with a random record id (SurrealDB will assign)
        res = self.conn.query(  # type: ignore
            "CREATE concept CONTENT { name: $name, desc: $desc, embedding: $embedding }",
            {"name": name, "desc": desc, "embedding": embedding},
        )

        # Parse response to get created id
        if isinstance(res, list) and len(res) > 0:
            items = res[0] if isinstance(res[0], list) else res
            if len(items) > 0 and isinstance(items[0], dict):
                return str(items[0].get("id"))  # type: ignore

        return ""

    def create_mention(
        self, doc_id: str, concept_id: str, desc: Optional[str] = None
    ) -> bool:
        """Create a mentions edge if it does not already exist. Returns True if created, False if skipped."""
        if self.conn is None:
            return False

        # Parse record ids into table and id parts
        if ":" in doc_id:
            in_table, in_id = doc_id.split(":", 1)
        else:
            in_table, in_id = "doc", doc_id

        if ":" in concept_id:
            out_table, out_id = concept_id.split(":", 1)
        else:
            out_table, out_id = "concept", concept_id

        # Check if the mentions relation already exists
        try:
            res = self.conn.query(
                "SELECT * FROM mentions WHERE `in` = type::thing($in_table, $in_id) AND `out` = type::thing($out_table, $out_id)",
                {
                    "in_table": in_table,
                    "in_id": in_id,
                    "out_table": out_table,
                    "out_id": out_id,
                },
            )
        except Exception:
            res = None

        # Normalize result and determine existence
        exists = False
        if isinstance(res, list) and len(res) > 0:
            first = res[0]
            if (
                isinstance(first, dict)
                and "result" in first
                and isinstance(first["result"], list)
            ):
                exists = len(first["result"]) > 0
            elif isinstance(first, list):
                exists = len(first) > 0
            elif all(isinstance(item, dict) for item in res):
                exists = len(res) > 0

        if exists:
            return False

        # Create the relation
        self.conn.query(
            f"RELATE {doc_id}->mentions->{concept_id} SET desc = $desc",
            {"desc": desc},
        )
        return True

    def create_related(
        self, concept1_id: str, concept2_id: str, desc: Optional[str] = None
    ) -> bool:
        """Create a related edge if it does not already exist. Returns True if created, False if skipped."""
        if self.conn is None:
            return False

        # Parse record ids into table and id parts
        if ":" in concept1_id:
            in_table, in_id = concept1_id.split(":", 1)
        else:
            in_table, in_id = "concept", concept1_id

        if ":" in concept2_id:
            out_table, out_id = concept2_id.split(":", 1)
        else:
            out_table, out_id = "concept", concept2_id

        # Check if the related relation already exists
        try:
            res = self.conn.query(
                "SELECT * FROM related WHERE `in` = type::thing($in_table, $in_id) AND `out` = type::thing($out_table, $out_id)",
                {
                    "in_table": in_table,
                    "in_id": in_id,
                    "out_table": out_table,
                    "out_id": out_id,
                },
            )
        except Exception:
            res = None

        # Normalize result and determine existence
        exists = False
        if isinstance(res, list) and len(res) > 0:
            first = res[0]
            if (
                isinstance(first, dict)
                and "result" in first
                and isinstance(first["result"], list)
            ):
                exists = len(first["result"]) > 0
            elif isinstance(first, list):
                exists = len(first) > 0
            elif all(isinstance(item, dict) for item in res):
                exists = len(res) > 0

        if exists:
            return False

        # Create the relation
        self.conn.query(
            f"RELATE {concept1_id}->related->{concept2_id} SET desc = $desc",
            {"desc": desc},
        )
        return True

    def get_all_docs(self) -> list[dict]:
        """Get all documents"""
        if self.conn is None:
            return []
        result = self.conn.select("doc")
        return result or []  # type: ignore

    def get_all_concepts(self) -> list[dict]:
        """Get all concepts"""
        if self.conn is None:
            return []
        result = self.conn.select("concept")
        return result or []  # type: ignore

    def get_all_mentions(self) -> list[dict]:
        """Get all mentions edges"""
        if self.conn is None:
            return []
        result = self.conn.query("SELECT * FROM mentions")
        if not result:
            return []
        # Handle different result formats returned by SurrealDB client:
        # - [{'result': [...]}]
        # - [ {row1}, {row2}, ... ]
        first = result[0]
        if isinstance(first, dict):
            # Standard client returns a dict with 'result' key
            if "result" in first and isinstance(first["result"], list):
                return first["result"]  # type: ignore
            # Some clients return rows directly as a list of dicts
            if all(
                isinstance(item, dict) and ("in" in item or "out" in item)
                for item in result
            ):
                return result  # type: ignore
        # In some cases the first element may itself be a list of rows
        if isinstance(first, list):
            return first  # type: ignore
        return []

    def get_all_related(self) -> list[dict]:
        """Get all related edges"""
        if self.conn is None:
            return []
        result = self.conn.query("SELECT * FROM related")
        if not result:
            return []
        # Normalize common return formats
        first = result[0]
        if isinstance(first, dict):
            if "result" in first and isinstance(first["result"], list):
                return first["result"]  # type: ignore
            if all(
                isinstance(item, dict) and ("in" in item or "out" in item)
                for item in result
            ):
                return result  # type: ignore
        if isinstance(first, list):
            return first  # type: ignore
        return []

    def get_doc(self, doc_id: str) -> Optional[dict]:
        """Get a document by ID (normalize to a single dict)"""
        if self.conn is None:
            return None
        result = self.conn.select(doc_id)
        if not result:
            return None
        # Normalize result to a single dict if wrapped in lists
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            item = result[0] if len(result) > 0 else None
            if isinstance(item, dict):
                return item
            if isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
                return item[0]
        return None

    def get_chunks_by_doc(self, doc_id: str) -> list[dict]:
        """Return a list of chunk records belonging to the given document ID."""
        if self.conn is None:
            return []
        result = self.conn.select("chunk")
        if not result:
            return []

        # Helper to normalize chunk.source to a string id
        def _source_to_id(val) -> str:
            if val is None:
                return ""
            if hasattr(val, "table_name") and hasattr(val, "record_id"):
                try:
                    return f"{val.table_name}:{val.record_id}"
                except Exception:
                    return str(val)
            if isinstance(val, dict):
                if "id" in val:
                    return str(val["id"])
                if "table" in val and "id" in val:
                    return f"{val['table']}:{val['id']}"
                return str(val)
            return str(val)

        chunks = []
        # result may be [row1, row2...] or [[row1, row2...]]
        rows = result[0] if isinstance(result[0], list) else result
        for item in rows:
            if isinstance(item, dict):
                src = _source_to_id(item.get("source"))
                if src == doc_id:
                    chunks.append(item)
        return chunks

    def get_concept(self, concept_id: str) -> Optional[dict]:
        """Get a concept by ID (normalize to a single dict)"""
        if self.conn is None:
            return None
        result = self.conn.select(concept_id)
        if not result:
            return None
        # Normalize result to a single dict if wrapped in lists
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            item = result[0] if len(result) > 0 else None
            if isinstance(item, dict):
                return item
            if isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
                return item[0]
        return None

    def vector_search_docs(
        self, embedding: list[float], limit: int = 5
    ) -> list[tuple[dict, float]]:
        """Search documents by vector similarity via chunks"""
        if self.conn is None:
            return []

        # Search chunks first, then get unique documents
        # Note: KNN limit must be a literal number, not a parameter
        chunk_limit = min(limit * 3, 30)  # Get more chunks to ensure enough docs
        result = self.conn.query(  # type: ignore
            f"""
            SELECT 
                source.* as doc,
                (1 - vector::distance::knn()) as similarity
            FROM chunk
            WHERE embedding <|{chunk_limit}|> $embedding
            ORDER BY similarity DESC
            """,
            {"embedding": embedding},  # type: ignore
        )

        if isinstance(result, list) and len(result) > 0:
            # Group by doc id and take max similarity
            doc_map = {}
            for item in result:
                if isinstance(item, dict) and "doc" in item:
                    doc = item["doc"]
                    if isinstance(doc, dict) and "id" in doc:
                        doc_id = str(doc["id"])
                        similarity = item.get("similarity", 0.0)
                        if doc_id not in doc_map or similarity > doc_map[doc_id][1]:
                            doc_map[doc_id] = (doc, similarity)

            # Sort by similarity and limit
            sorted_docs = sorted(doc_map.values(), key=lambda x: x[1], reverse=True)[
                :limit
            ]
            return sorted_docs
        return []

    def vector_search_concepts(
        self, embedding: list[float], limit: int = 5
    ) -> list[tuple[dict, float]]:
        """Search concepts by vector similarity using KNN"""
        if self.conn is None:
            return []

        result = self.conn.query(  # type: ignore
            f"""
            SELECT 
                *,
                vector::similarity::cosine(embedding, $embedding) as similarity
            FROM concept
            ORDER BY similarity DESC
            LIMIT $limit
            """,
            {"embedding": embedding, "limit": limit},  # type: ignore
        )

        # Expect either a list of row dicts or a list whose first element is a list of rows.
        if isinstance(result, list) and len(result) > 0:
            return [
                (item, item.get("similarity", 0.0))
                for item in result  # type: ignore
                if isinstance(item, dict)
            ]
        return []

    def vector_search_chunks(
        self, embedding: list[float], limit: int = 10
    ) -> list[tuple[dict, float]]:
        """Search chunks by vector similarity using KNN"""
        if self.conn is None:
            return []

        result = self.conn.query(  # type: ignore
            """
            SELECT 
                *,
                vector::similarity::cosine(embedding, $embedding) as similarity
            FROM chunk
            ORDER BY similarity DESC
            LIMIT $limit
            """,
            {"embedding": embedding, "limit": limit},  # type: ignore
        )

        # Expect either a list of row dicts or a list whose first element is a list of rows.
        if isinstance(result, list) and len(result) > 0:
            return [
                (item, item.get("similarity", 0.0))
                for item in result  # type: ignore
                if isinstance(item, dict)
            ]
        return []

    def delete_doc(self, doc_id: str):
        """Delete a document by ID and its related chunks/mentions.

        SurrealDB does not automatically cascade-delete arbitrary related records
        (chunks are stored with a 'source' record reference), so explicitly
        remove related chunks and mentions before deleting the document.
        """
        if self.conn is None:
            return

        # Parse source id like "doc:abcd" or just "abcd"
        if ":" in doc_id:
            table, record_id = doc_id.split(":", 1)
        else:
            table, record_id = "doc", doc_id

        # Delete chunks that reference this document (chunk.source is a record<doc>)
        try:
            self.conn.query(
                "DELETE FROM chunk WHERE source = type::thing($table, $record_id)",
                {"table": table, "record_id": record_id},
            )
        except Exception:
            # Best-effort: don't fail on errors during cleanup
            pass

        # Delete mentions edges where this document is the 'in' side
        try:
            self.conn.query(
                "DELETE FROM mentions WHERE `in` = type::thing($table, $record_id)",
                {"table": table, "record_id": record_id},
            )
        except Exception:
            pass

        # Finally delete the document itself
        self.conn.delete(doc_id)


# Global database instance
db = Database()
