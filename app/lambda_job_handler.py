# Generic Lambda entry for jobs: dispatch by JOB_NAME env var
import os
import sys

from app.jobs import ingest_1d as j1d
from app.jobs import ingest_1h as j1h
from app.jobs import train_daily as jtrain

def handler(event, context):
    job = os.getenv("JOB_NAME", "")
    symbols = os.getenv("SYMBOLS", "AAPL,MSFT").split(",")
    out = "/tmp/data"
    os.makedirs(out, exist_ok=True)

    if job == "ingest_1d":
        sys.argv = ["ingest_1d", "--symbols", ",".join(symbols), "--out", out]
        j1d.main()
        return {"status": "ok", "job": job}
    elif job == "ingest_1h":
        sys.argv = ["ingest_1h", "--symbols", ",".join(symbols), "--out", out]
        j1h.main()
        return {"status": "ok", "job": job}
    elif job == "train_daily":
        sys.argv = ["train_daily", "--symbols", ",".join(symbols), "--data", out]
        jtrain.main()
        return {"status": "ok", "job": job}
    else:
        return {"status": "noop", "reason": "Unknown JOB_NAME"}
