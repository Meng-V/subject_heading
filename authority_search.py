"""Authority search using Weaviate for LCSH and FAST vocabularies.

MVP Scope:
- Actively generate candidates for LCSH and FAST only
- Other vocabularies (GTT, RERO, SWD, etc.) are optional/future extensions
- Designed for East Asian collection in US academic library
"""
import weaviate
from weaviate.classes.query import MetadataQuery
from typing import List, Optional, Dict
from openai import OpenAI

from config import settings
from models import AuthorityCandidate, TopicMatchResult, TopicCandidate


class AuthorityVectorSearch:
    """Handles authority heading search for LCSH and FAST vocabularies using Weaviate."""
    
    # MVP vocabularies (actively generated)
    MVP_VOCABULARIES = ["lcsh", "fast"]
    
    # Future extension vocabularies (display/preserve only)
    FUTURE_VOCABULARIES = ["gtt", "rero", "swd", "idszbz", "ram"]
    
    # All supported vocabularies
    VOCABULARIES = MVP_VOCABULARIES + FUTURE_VOCABULARIES
    
    def __init__(self):
        """Initialize Weaviate client and OpenAI for embeddings."""
        self.weaviate_url = settings.weaviate_url
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.client = None
        
    def connect(self):
        """Connect to Weaviate instance."""
        try:
            # Parse URL to extract host and port
            from urllib.parse import urlparse
            parsed = urlparse(self.weaviate_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8080
            
            self.client = weaviate.connect_to_local(
                host=host,
                port=port
            )
            return True
        except Exception as e:
            print(f"Failed to connect to Weaviate: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from Weaviate."""
        if self.client:
            self.client.close()
    
    def initialize_schemas(self):
        """Initialize authority collection schemas for MVP vocabularies (LCSH + FAST)."""
        if not self.client:
            self.connect()
        
        # MVP: Only create LCSH and FAST collections
        collections_to_create = [
            ("LCSHSubject", "Library of Congress Subject Headings - primary authority for 650/651/655"),
            ("FASTSubject", "FAST (Faceted Application of Subject Terminology) - linked data vocabulary"),
        ]
        
        # Future extensions (commented out for MVP)
        # ("GTTSubject", "GTT Authority"),
        # ("REROSubject", "RERO Authority"),
        # ("SWDSubject", "SWD Authority"),
        
        for collection_name, description in collections_to_create:
            try:
                if self.client.collections.exists(collection_name):
                    print(f"{collection_name} collection already exists")
                    continue
                
                self.client.collections.create(
                    name=collection_name,
                    # No vectorizer - we provide vectors manually
                    vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none(),
                    properties=[
                        weaviate.classes.config.Property(
                            name="label",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            description="Authority label"
                        ),
                        weaviate.classes.config.Property(
                            name="uri",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            description="Authority URI"
                        ),
                        weaviate.classes.config.Property(
                            name="vocabulary",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            skip_vectorization=True,
                            description="Vocabulary code"
                        ),
                        weaviate.classes.config.Property(
                            name="subject_type",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            skip_vectorization=True,
                            description="Subject type: topical, geographic, or genre_form"
                        ),
                        weaviate.classes.config.Property(
                            name="alt_labels",
                            data_type=weaviate.classes.config.DataType.TEXT_ARRAY,
                            skip_vectorization=False,
                            description="Alternative labels (altLabel)"
                        ),
                        weaviate.classes.config.Property(
                            name="broader_terms",
                            data_type=weaviate.classes.config.DataType.TEXT_ARRAY,
                            skip_vectorization=True,
                            description="Broader term URIs"
                        ),
                        weaviate.classes.config.Property(
                            name="narrower_terms",
                            data_type=weaviate.classes.config.DataType.TEXT_ARRAY,
                            skip_vectorization=True,
                            description="Narrower term URIs"
                        ),
                        weaviate.classes.config.Property(
                            name="scope_note",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            skip_vectorization=False,
                            description="Usage notes and scope"
                        ),
                        weaviate.classes.config.Property(
                            name="language",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            skip_vectorization=True,
                            description="Language code (optional)"
                        ),
                        weaviate.classes.config.Property(
                            name="broader",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            skip_vectorization=True,
                            description="Broader terms (legacy, use broader_terms)"
                        ),
                        weaviate.classes.config.Property(
                            name="narrower",
                            data_type=weaviate.classes.config.DataType.TEXT,
                            skip_vectorization=True,
                            description="Narrower terms (legacy, use narrower_terms)"
                        ),
                    ]
                )
                print(f"✅ Created {collection_name} collection")
                
            except Exception as e:
                print(f"❌ Failed to create {collection_name}: {str(e)}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def _get_collection_for_vocab(self, vocabulary: str) -> str:
        """Map vocabulary code to Weaviate collection name."""
        vocab_map = {
            "lcsh": "LCSHSubject",
            "fast": "FASTSubject",
            "gtt": "GTTSubject",
            "rero": "REROSubject",
            "swd": "SWDSubject"
        }
        return vocab_map.get(vocabulary.lower(), "LCSHSubject")
    
    def index_authority_entry(
        self,
        label: str,
        uri: str,
        vocabulary: str,
        language: str = "",
        broader: str = "",
        narrower: str = ""
    ):
        """
        Index a single authority entry into appropriate Weaviate collection.
        
        Args:
            label: Authority label
            uri: Authority URI
            vocabulary: Vocabulary code (lcsh, fast, gtt, rero, swd, etc.)
            language: Language code (optional)
            broader: Broader terms (optional)
            narrower: Narrower terms (optional)
        """
        if not self.client:
            self.connect()
        
        try:
            # Generate embedding
            embedding = self._generate_embedding(label)
            
            # Get collection
            collection_name = self._get_collection_for_vocab(vocabulary)
            collection = self.client.collections.get(collection_name)
            
            # Insert with vector
            collection.data.insert(
                properties={
                    "label": label,
                    "uri": uri,
                    "vocabulary": vocabulary.lower(),
                    "language": language,
                    "broader": broader,
                    "narrower": narrower
                },
                vector=embedding
            )
            
        except Exception as e:
            raise Exception(f"Failed to index authority entry: {str(e)}")
    
    def batch_index_authorities(self, entries: List[Dict], vocabulary: str):
        """
        Batch index multiple authority entries.
        
        Args:
            entries: List of dicts with keys: label, uri, language (optional), broader (optional), narrower (optional)
            vocabulary: Vocabulary code for all entries
        """
        if not self.client:
            self.connect()
        
        try:
            collection_name = self._get_collection_for_vocab(vocabulary)
            collection = self.client.collections.get(collection_name)
            
            # Batch insert
            with collection.batch.dynamic() as batch:
                for entry in entries:
                    label = entry.get("label", "")
                    if not label:
                        continue
                    
                    # Generate embedding
                    embedding = self._generate_embedding(label)
                    
                    batch.add_object(
                        properties={
                            "label": label,
                            "uri": entry.get("uri", ""),
                            "vocabulary": vocabulary.lower(),
                            "language": entry.get("language", ""),
                            "broader": entry.get("broader", ""),
                            "narrower": entry.get("narrower", "")
                        },
                        vector=embedding
                    )
            
            print(f"✅ Batch indexed {len(entries)} {vocabulary.upper()} entries")
            
        except Exception as e:
            raise Exception(f"Failed to batch index: {str(e)}")
    
    async def search_authorities(
        self,
        topic: str,
        vocabularies: List[str] = None,
        limit_per_vocab: int = 5,
        min_score: float = 0.7
    ) -> List[AuthorityCandidate]:
        """
        Search for authority matches across multiple vocabularies.
        
        Args:
            topic: Semantic topic to search for
            vocabularies: List of vocabulary codes to search (default: ["lcsh", "fast"])
            limit_per_vocab: Maximum results per vocabulary
            min_score: Minimum certainty threshold
            
        Returns:
            List of AuthorityCandidate objects
        """
        if not self.client:
            self.connect()
        
        if vocabularies is None:
            vocabularies = ["lcsh", "fast"]
        
        try:
            # Generate embedding for the topic
            topic_embedding = self._generate_embedding(topic)
            
            all_candidates = []
            
            # Search each vocabulary
            for vocab in vocabularies:
                collection_name = self._get_collection_for_vocab(vocab)
                
                try:
                    collection = self.client.collections.get(collection_name)
                    
                    # Perform vector search
                    response = collection.query.near_vector(
                        near_vector=topic_embedding,
                        limit=limit_per_vocab,
                        return_metadata=MetadataQuery(certainty=True)
                    )
                    
                    # Parse results
                    for obj in response.objects:
                        if obj.metadata.certainty and obj.metadata.certainty >= min_score:
                            all_candidates.append(AuthorityCandidate(
                                label=obj.properties.get("label", ""),
                                uri=obj.properties.get("uri", ""),
                                vocabulary=obj.properties.get("vocabulary", vocab),
                                score=obj.metadata.certainty
                            ))
                
                except Exception as e:
                    print(f"Warning: Failed to search {vocab}: {str(e)}")
                    continue
            
            # Sort by score descending
            all_candidates.sort(key=lambda x: x.score, reverse=True)
            
            return all_candidates
            
        except Exception as e:
            raise Exception(f"Authority search failed: {str(e)}")
    
    async def search_multiple_topics(
        self,
        topics: List[TopicCandidate],
        vocabularies: List[str] = None,
        limit_per_vocab: int = 5,
        min_score: float = 0.7
    ) -> List[TopicMatchResult]:
        """
        Search authority matches for multiple topics.
        
        Args:
            topics: List of TopicCandidate objects
            vocabularies: List of vocabularies to search
            limit_per_vocab: Maximum results per vocabulary per topic
            min_score: Minimum score threshold
            
        Returns:
            List of TopicMatchResult objects
        """
        results = []
        
        for topic_candidate in topics:
            candidates = await self.search_authorities(
                topic=topic_candidate.topic,
                vocabularies=vocabularies,
                limit_per_vocab=limit_per_vocab,
                min_score=min_score
            )
            
            results.append(TopicMatchResult(
                topic=topic_candidate.topic,
                topic_type=topic_candidate.type,
                authority_candidates=candidates,
                matches=[]  # Legacy field
            ))
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about MVP authority indexes (LCSH + FAST only)."""
        if not self.client:
            self.connect()
        
        stats = {}
        
        # Only query MVP vocabularies
        for vocab in self.MVP_VOCABULARIES:
            try:
                collection_name = self._get_collection_for_vocab(vocab)
                collection = self.client.collections.get(collection_name)
                aggregate = collection.aggregate.over_all(total_count=True)
                stats[vocab] = aggregate.total_count
            except Exception as e:
                stats[vocab] = f"error: {str(e)}"
        
        return stats


# Global authority search instance
authority_search = AuthorityVectorSearch()
