"""LCSH vector search module using Weaviate."""
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery
from typing import List, Optional
from openai import OpenAI

from config import settings
from models import LCSHMatch, TopicMatchResult


class LCSHVectorSearch:
    """Handles LCSH authority heading search using Weaviate vector database."""
    
    def __init__(self):
        """Initialize Weaviate client and OpenAI for embeddings."""
        self.weaviate_url = settings.weaviate_url
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.client = None
        
    def connect(self):
        """Connect to Weaviate instance."""
        try:
            self.client = weaviate.connect_to_local(
                host=self.weaviate_url.replace("http://", "").replace(":8080", ""),
                port=8080
            )
            return True
        except Exception as e:
            print(f"Failed to connect to Weaviate: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from Weaviate."""
        if self.client:
            self.client.close()
    
    def initialize_schema(self):
        """Initialize LCSH collection schema in Weaviate."""
        if not self.client:
            self.connect()
        
        try:
            # Check if collection exists
            if self.client.collections.exists("LCSH"):
                print("LCSH collection already exists")
                return
            
            # Create collection with vectorizer configuration
            self.client.collections.create(
                name="LCSH",
                vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none(),
                properties=[
                    weaviate.classes.config.Property(
                        name="label",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="LCSH authority label"
                    ),
                    weaviate.classes.config.Property(
                        name="uri",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="id.loc.gov URI"
                    ),
                    weaviate.classes.config.Property(
                        name="broader",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        skip_vectorization=True,
                        description="Broader terms (optional)"
                    ),
                    weaviate.classes.config.Property(
                        name="narrower",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        skip_vectorization=True,
                        description="Narrower terms (optional)"
                    )
                ]
            )
            print("LCSH collection created successfully")
            
        except Exception as e:
            raise Exception(f"Failed to initialize schema: {str(e)}")
    
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
    
    def index_lcsh_entry(
        self,
        label: str,
        uri: str,
        broader: str = "",
        narrower: str = ""
    ):
        """
        Index a single LCSH entry into Weaviate.
        
        Args:
            label: LCSH authority label
            uri: id.loc.gov URI
            broader: Broader terms (optional)
            narrower: Narrower terms (optional)
        """
        if not self.client:
            self.connect()
        
        try:
            # Generate embedding
            embedding = self._generate_embedding(label)
            
            # Get collection
            lcsh_collection = self.client.collections.get("LCSH")
            
            # Insert with vector
            lcsh_collection.data.insert(
                properties={
                    "label": label,
                    "uri": uri,
                    "broader": broader,
                    "narrower": narrower
                },
                vector=embedding
            )
            
        except Exception as e:
            raise Exception(f"Failed to index LCSH entry: {str(e)}")
    
    def batch_index_lcsh(self, entries: List[dict]):
        """
        Batch index multiple LCSH entries.
        
        Args:
            entries: List of dicts with keys: label, uri, broader (optional), narrower (optional)
        """
        if not self.client:
            self.connect()
        
        try:
            lcsh_collection = self.client.collections.get("LCSH")
            
            # Batch insert
            with lcsh_collection.batch.dynamic() as batch:
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
                            "broader": entry.get("broader", ""),
                            "narrower": entry.get("narrower", "")
                        },
                        vector=embedding
                    )
            
            print(f"Batch indexed {len(entries)} LCSH entries")
            
        except Exception as e:
            raise Exception(f"Failed to batch index LCSH entries: {str(e)}")
    
    async def search_lcsh(
        self,
        topic: str,
        limit: int = 10,
        certainty: float = 0.7
    ) -> List[LCSHMatch]:
        """
        Search for LCSH matches for a given topic.
        
        Args:
            topic: Semantic topic to search for
            limit: Maximum number of results
            certainty: Minimum certainty threshold (0-1)
            
        Returns:
            List of LCSHMatch objects
        """
        if not self.client:
            self.connect()
        
        try:
            # Generate embedding for the topic
            topic_embedding = self._generate_embedding(topic)
            
            # Get collection
            lcsh_collection = self.client.collections.get("LCSH")
            
            # Perform vector search
            response = lcsh_collection.query.near_vector(
                near_vector=topic_embedding,
                limit=limit,
                return_metadata=MetadataQuery(certainty=True)
            )
            
            # Parse results
            matches = []
            for obj in response.objects:
                # Filter by certainty threshold
                if obj.metadata.certainty and obj.metadata.certainty >= certainty:
                    matches.append(LCSHMatch(
                        label=obj.properties.get("label", ""),
                        uri=obj.properties.get("uri", ""),
                        certainty=obj.metadata.certainty
                    ))
            
            return matches
            
        except Exception as e:
            raise Exception(f"LCSH search failed: {str(e)}")
    
    async def search_multiple_topics(
        self,
        topics: List[str],
        limit_per_topic: int = 10,
        certainty: float = 0.7
    ) -> List[TopicMatchResult]:
        """
        Search LCSH matches for multiple topics.
        
        Args:
            topics: List of semantic topics
            limit_per_topic: Maximum results per topic
            certainty: Minimum certainty threshold
            
        Returns:
            List of TopicMatchResult objects
        """
        results = []
        
        for topic in topics:
            matches = await self.search_lcsh(topic, limit_per_topic, certainty)
            results.append(TopicMatchResult(
                topic=topic,
                matches=matches
            ))
        
        return results
    
    def get_stats(self) -> dict:
        """Get statistics about the LCSH index."""
        if not self.client:
            self.connect()
        
        try:
            lcsh_collection = self.client.collections.get("LCSH")
            aggregate = lcsh_collection.aggregate.over_all(total_count=True)
            
            return {
                "total_entries": aggregate.total_count,
                "collection_name": "LCSH"
            }
        except Exception as e:
            return {"error": str(e)}


# Global LCSH search instance
lcsh_search = LCSHVectorSearch()
