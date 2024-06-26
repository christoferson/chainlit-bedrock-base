import time
import boto3

def transcribe_file(job_name, file_uri, transcribe_client) -> str:

    transcript_file_uri = None

    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": file_uri},
        MediaFormat="wav",
        #LanguageCode="en-US",
        IdentifyLanguage=True, #IdentifyMultipleLanguages 
    )

    max_tries = 60
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]
        if job_status in ["COMPLETED", "FAILED"]:
            print(f"Job {job_name} is {job_status}.")
            if job_status == "COMPLETED":
                transcript_file_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                print(
                    f"Download the transcript from\n"
                    f"\t{transcript_file_uri}."
                )
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)

    return transcript_file_uri