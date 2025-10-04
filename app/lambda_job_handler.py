# Generic Lambda entry for jobs: dispatch by JOB_NAME from event
from app.jobs import ingest_1d as j1d
from app.jobs import ingest_1h as j1h
from app.jobs import train_daily as jtrain

def handler(event, context):
    """
    Generic Lambda handler that routes to specific job handlers based on JOB_NAME in event
    """
    # Get job name from event (sent by EventBridge)
    job_name = event.get("JOB_NAME", "")
    
    print(f"🚀 Generic job handler received: {job_name}")
    print(f"Event: {event}")
    
    # Route to appropriate job handler
    if job_name == "ingest_1d":
        return j1d.lambda_handler(event, context)
    elif job_name == "ingest_1h":
        return j1h.lambda_handler(event, context)
    elif job_name == "train_daily":
        return jtrain.lambda_handler(event, context)
    else:
        print(f"⚠️ Unknown JOB_NAME: {job_name}")
        return {"statusCode": 400, "body": {"error": f"Unknown JOB_NAME: {job_name}"}}
