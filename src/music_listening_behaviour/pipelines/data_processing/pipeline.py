"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.18.12
"""

from kedro.pipeline import Pipeline, node, pipeline
from .nodes import preprocess_format_tracksessions, process_tracksessions
from kedro.io import MemoryDataset

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([ 
        node( 
                func=preprocess_format_tracksessions,
                inputs= ["track_sessions", "userid_profiles", "parameters"],
                outputs="ts_formatted",
                name="preprocess_format_tracksessions",
            ),
        node( 
                func=process_tracksessions,
                inputs= ["ts_formatted", "parameters"],
                outputs="results_summary",
                name="process_summarize_tracksessions",
            ),            
    ])
