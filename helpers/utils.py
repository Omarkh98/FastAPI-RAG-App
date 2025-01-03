import os
import sys
import json
import numpy as np
import faiss
from helpers.exception import CustomException
from helpers.logger import logging
from sentence_transformers import SentenceTransformer

def save_vector_db(embeddings, chunks, index_file, metadata_file):
    try:
        # Save FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings))
        faiss.write_index(index, index_file)

        # Save metadata as JSONL
        with open(metadata_file, "w") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + "\n")
        
        logging.info("Data Saved To Vector DB (FAISS and JSONL)!")
    except Exception as e:
        raise CustomException(e, sys)


def load_vector_db(index_file, metadata_file):
    try:
        # Check if the FAISS index file exists
        if not os.path.exists(index_file):
            print(f"FAISS index not found at {index_file}. Creating a new one...")
            create_vector_db_from_jsonl(metadata_file, index_file)

        # Load FAISS index
        print("Loading FAISS index...")
        index = faiss.read_index(index_file)

        # Load metadata from JSONL
        metadata = []
        with open(metadata_file, "r") as f:
            for line in f:
                metadata.append(json.loads(line.strip()))
        
        logging.info("Data Loaded From Vector DB Successfully (FAISS and JSONL)!")
        return index, metadata
    except Exception as e:
        raise CustomException(e, sys)


def create_vector_db_from_jsonl(metadata_file, index_file):
    try:
        # Load metadata from JSONL
        metadata = []
        with open(metadata_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())  # Parse each line as JSON
                    if isinstance(entry, list):  # Handle unexpected nested lists
                        metadata.extend(entry)
                    elif isinstance(entry, dict):  # Normal case
                        metadata.append(entry)
                    else:
                        print(f"Skipping unexpected entry type: {type(entry)}")
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON line: {line.strip()} (Error: {e})")

        # Validate metadata structure
        if not all(isinstance(entry, dict) and "text" in entry for entry in metadata):
            raise ValueError("Metadata entries must be dictionaries with a 'text' key.")

        # Initialize embedding model
        print("Initializing embedding model...")
        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

        # Generate embeddings for each chunk's text
        print("Generating embeddings for metadata...")
        embeddings = []
        for entry in metadata:
            try:
                embeddings.append(model.encode(entry["text"]))
            except KeyError:
                print(f"Skipping entry without 'text': {entry}")

        embeddings = np.array(embeddings, dtype="float32")  # Convert to NumPy array

        # Create FAISS index
        print("Creating FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings))

        # Save FAISS index
        print(f"Saving FAISS index to {index_file}...")
        faiss.write_index(index, index_file)

        print("FAISS index created and saved successfully.")

    except Exception as e:
        raise RuntimeError(f"Error creating FAISS index: {e}")
