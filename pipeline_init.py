from kokoro import KPipeline
import pickle
import os

def initialize_pipeline():
    print("Initializing Kokoro TTS pipeline...")
    pipeline = KPipeline(lang_code='a')
    
    # Save the pipeline to a file
    with open('pipeline.pkl', 'wb') as f:
        pickle.dump(pipeline, f)
    print("Pipeline initialized and saved successfully!")

if __name__ == "__main__":
    initialize_pipeline() 