import asyncio
from ..sensors.video.video_stream import VideoStream
from .video_target_recognition import VideoTargetRecognition

class RealTimeObjectDetection:
    def __init__(self):
        self.video_stream = VideoStream()
        self.target_recognition = VideoTargetRecognition()

    async def start_detection(self):
        async for frame in self.video_stream.stream_frames():
            detection_result = await self.target_recognition._process_frame_async(frame)
            # Process detection result
            print(detection_result)