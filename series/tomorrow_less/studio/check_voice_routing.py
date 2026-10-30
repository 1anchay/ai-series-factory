"""Offline tests: never mix speech engines within a published episode."""
import numpy as np
import voice

def run():
    shots=[{'voice':'Тест голоса Аси','speaker':'narrator'},
           {'voice':'Тест голоса Марка','speaker':'mark'},
           {'voice':'Тест голоса Ники','speaker':'nika'}]
    original_edge, original_piper, original_sleep=voice._edge,voice._piper,voice.time.sleep
    try:
        voice.time.sleep=lambda delay:None
        calls=[]
        def edge_fail_on_third(text,tmp,idx,voice_name,rate):
            calls.append(('edge',idx))
            if idx==2:raise RuntimeError('Simulated Edge rate limit')
            return np.ones(voice.SR,dtype=np.float32)*.14
        def piper_ok(text,tmp,idx,model_root,speaker):
            calls.append(('piper',idx,speaker))
            return np.ones(voice.SR,dtype=np.float32)*.12
        voice._edge=edge_fail_on_third
        voice._piper=piper_ok
        out=voice.synthesize(shots,'/tmp',mode='auto')
        assert len(out)==len(shots)
        assert all(tag.startswith('piper:') for _,tag in out),out
        assert ('piper',1,'mark') in calls
        voice._edge=lambda text,tmp,idx,voice_name,rate:np.ones(voice.SR,dtype=np.float32)*.14
        out2=voice.synthesize(shots,'/tmp',mode='auto')
        assert all(tag.startswith('edge:') for _,tag in out2),out2
        print('Voice route checks passed: coherent Edge/Piper engines and male role')
    finally:
        voice._edge,voice._piper,voice.time.sleep=original_edge,original_piper,original_sleep
if __name__=='__main__':run()
