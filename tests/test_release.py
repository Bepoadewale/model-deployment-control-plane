from modelcp.core import ModelVersion, Release, State, advance, digest


def models():
    c=ModelVersion("fraud","v1",b"champion","dataset-a","abc","features->score"); n=ModelVersion("fraud","v2",b"candidate","dataset-a","def","features->score"); return c,n
def metrics(model,accuracy=.93,recall=.88,p95=200): return {"artifact_digest":digest(model),"accuracy":accuracy,"region_b_recall":recall,"p95_ms":p95}
def test_success_needs_approval():
    c,n=models(); r=advance(Release("rel",n,c),metrics(c,.91,.88),metrics(n),False); assert r.state==State.PROMOTION_PENDING
    assert advance(Release("rel2",n,c),metrics(c,.91,.88),metrics(n),True).state==State.PRODUCTION
def test_slice_failure_rejects_aggregate_improvement():
    c,n=models(); assert advance(Release("x",n,c),metrics(c,.91,.88),metrics(n,.95,.70),True).state==State.EVALUATION_FAILED
def test_latency_failure_rolls_back():
    c,n=models(); assert advance(Release("x",n,c),metrics(c,.91,.88),metrics(n,p95=700),True).state==State.ROLLED_BACK
def test_digest_mismatch_fails_closed():
    c,n=models(); m=metrics(n); m["artifact_digest"]="wrong"; assert advance(Release("x",n,c),metrics(c,.91,.88),m,True).state==State.REJECTED
