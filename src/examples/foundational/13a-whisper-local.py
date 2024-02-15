import argparse
import asyncio
import wave
from dailyai.queue_frame import EndStreamQueueFrame, TranscriptionQueueFrame

from dailyai.services.local_transport_service import LocalTransportService
from dailyai.services.whisper_ai_services import WhisperSTTService


async def main(room_url: str):
    global transport
    global stt

    meeting_duration_minutes = 1
    transport = LocalTransportService(
        mic_enabled=True,
        camera_enabled=False,
        speaker_enabled=True,
        duration_minutes=meeting_duration_minutes,
        start_transcription = True
    )
    stt = WhisperSTTService()
    transcription_output_queue = asyncio.Queue()
    transport_done = asyncio.Event()

    async def handle_transcription():
        print("`````````TRANSCRIPTION`````````")
        while not transport_done.is_set():
            item = await transcription_output_queue.get()
            print("got item from queue", item)
            if isinstance(item, TranscriptionQueueFrame):
                print(item.text)
            elif isinstance(item, EndStreamQueueFrame):
                break
        print("handle_transcription done")

    async def handle_speaker():
        await stt.run_to_queue(
            transcription_output_queue, transport.get_receive_frames()
        )
        await transcription_output_queue.put(EndStreamQueueFrame())
        print("handle speaker done.")

    async def run_until_done():
        await transport.run()
        transport_done.set()
        print("run_until_done done")

    await asyncio.gather(run_until_done(), handle_speaker(), handle_transcription())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Daily Bot Sample")
    parser.add_argument(
        "-u", "--url", type=str, required=True, help="URL of the Daily room to join"
    )

    args, unknown = parser.parse_known_args()
    asyncio.run(main(args.url))