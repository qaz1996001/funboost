# -*- coding: utf-8 -*-
"""
Funboost Workflow Example - Video Processing Pipeline

Demonstrates using chain + chord to implement a classic video processing workflow:
1. Download video
2. Transcode to multiple resolutions in parallel
3. Aggregate results and send notification

This is a classic Celery Canvas use case, implemented with Funboost Workflow.

How to run:
    cd d:\\codes\\funboost
    D:\\ProgramData\\Miniconda3\\envs\\py39b\\python.exe funboost/workflow/examples/video_pipeline.py
"""

import time
import typing

from funboost import boost, ctrl_c_recv, BrokerEnum, fct
from funboost.workflow import chain, group, chord, WorkflowBoosterParams


# ============================================================
# Define workflow tasks
# ============================================================

class VideoWorkflowParams(WorkflowBoosterParams):
    """Common parameters for the video processing workflow"""
    broker_kind: str = BrokerEnum.SQLITE_QUEUE
    broker_exclusive_config: dict = {'pull_msg_batch_size': 1}
    max_retry_times: int = 0


@boost(VideoWorkflowParams(queue_name='wf_download_video'))
def download_video(url: str) -> str:
    """
    Step 1: Download video

    :param url: Video URL
    :return: Local file path after download
    """
    print(fct.full_msg)
    fct.logger.info(f'Starting video download: {url}')

    # Simulate download time
    time.sleep(2)
    
    file_path = f'/downloads/{url.replace("://", "_").replace("/", "_")}'
    fct.logger.info(f'Download complete: {file_path}')
    
    return file_path


@boost(VideoWorkflowParams(queue_name='wf_transform_video'))
def transform_video(video_file: str, resolution: str = '360p') -> str:
    """
    Step 2: Transcode video

    :param video_file: Input video file path
    :param resolution: Target resolution
    :return: Transcoded file path
    """
    print(fct.full_msg)
    fct.logger.info(f'Starting transcode: {video_file} -> {resolution}')

    # Simulate transcode time
    time.sleep(3)
    
    output_file = f'{video_file}_{resolution}.mp4'
    fct.logger.info(f'Transcode complete: {output_file}')
    
    return output_file


@boost(VideoWorkflowParams(queue_name='wf_send_finish_msg'))
def send_finish_msg(video_list: typing.List[str], url: str) -> str:
    """
    Step 3: Send completion notification

    :param video_list: List of transcoded video files
    :param url: Original video URL
    :return: Completion message
    """
    print(fct.full_msg)
    fct.logger.info('Sending completion notification...')
    fct.logger.info(f'   Original video: {url}')
    fct.logger.info(f'   Transcode results: {video_list}')
    
    # Simulate sending notification
    time.sleep(1)
    
    msg = f'Video processing complete! {url} -> {len(video_list)} resolution versions'
    fct.logger.info(f'{msg}')
    
    return msg


# ============================================================
# Workflow orchestration
# ============================================================

def create_video_pipeline(url: str):
    """
    Create a video processing workflow

    Equivalent to Celery Canvas:
    ```python
    chain(
        download_video.s(url),
        chord(
            group(transform_video.s(r) for r in ['360p', '720p', '1080p']),
            send_finish_msg.s(url=url)
        )
    )
    ```
    
    Note: After importing funboost.workflow, all @boost decorated functions automatically have .s() and .si() methods.
    No manual addition needed!
    """
    # Define workflow
    resolutions = ['360p', '720p', '1080p']
    
    workflow = chain(
        download_video.s(url),
        chord(
            group(transform_video.s(resolution=r) for r in resolutions),
            send_finish_msg.s(url=url)
        )
    )
    
    return workflow


# ============================================================
# Main program
# ============================================================

if __name__ == '__main__':
    print('=' * 60)
    print('Funboost Workflow Example - Video Processing Pipeline')
    print('=' * 60)
    
    # Start consumers
    print('\nStarting consumers...')
    download_video.consume()
    transform_video.consume()
    send_finish_msg.consume()
    
    # Wait for consumers to be ready
    time.sleep(3)
    
    # Create and execute workflow
    print('\nExecuting video processing workflow...')
    print('-' * 60)
    
    url = 'https://example.com/video.mp4'
    workflow = create_video_pipeline(url)
    
    # Execute workflow synchronously
    rpc_data = workflow.apply()
    
    print('-' * 60)
    print('\nWorkflow execution complete!')
    print(f'   Final result: {rpc_data}')
    print('=' * 60)
    
    # Keep running
    ctrl_c_recv()
