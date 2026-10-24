"""CPU adapter for the repository's upstream DMRST code, in isolated module namespace.

AST changes only replace .cuda() tensor transfers with .to('cpu'). Source files
remain unchanged. A missing/mismatched checkpoint is an error, never a fake tree.
"""
import ast
import contextlib
import hashlib
import json
import re
import sys
import types
from pathlib import Path


class CPUTransfers(ast.NodeTransformer):
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and node.func.attr=='cuda':
            node.func.attr='to';node.args=[ast.Constant(value='cpu')];node.keywords=[]
        return node


def load_module(name,path):
    module=types.ModuleType(name);module.__file__=str(path)
    sys.modules[name]=module
    tree=ast.fix_missing_locations(CPUTransfers().visit(ast.parse(path.read_text(encoding='utf-8-sig'))))
    exec(compile(tree,str(path),'exec'),module.__dict__)
    return module


def main():
    import torch
    import random
    import numpy as np
    from transformers import AutoTokenizer,AutoModel
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.backends.mkldnn.enabled=False
    source=Path(__file__).resolve().parents[3]/'sanctuary_v2/models/dmrst_parser'
    checkpoint,backbone=map(Path,sys.argv[1:3])
    with contextlib.redirect_stdout(sys.stderr):
        load_module('config',source/'config.py')
        load_module('DataHandler',source/'DataHandler.py')
        load_module('module',source/'module.py')
        architecture=load_module('model_depth',source/'model_depth.py')
        tokenizer=AutoTokenizer.from_pretrained(str(backbone),use_fast=True,local_files_only=True)
        encoder=AutoModel.from_pretrained(str(backbone),local_files_only=True)
        model=architecture.ParsingNet(encoder,bert_tokenizer=tokenizer).cpu()
        state=torch.load(checkpoint,map_location='cpu',weights_only=True)
        # Transformers now registers this deterministic position buffer as nonpersistent.
        # Validate before removing this one legacy key; all learned weights stay strict.
        key='encoder.language_model.embeddings.position_ids'
        if key in state and key not in model.state_dict():
            expected=model.encoder.language_model.embeddings.position_ids.cpu()
            if not torch.equal(state[key].cpu(),expected):raise ValueError('Legacy position_ids mismatch')
            state.pop(key)
        model.load_state_dict(state,strict=True)
        del state
        model.eval()
    hasher=hashlib.sha256()
    with checkpoint.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):hasher.update(chunk)
    digest=hasher.hexdigest()
    for line in sys.stdin:
        try:
            text=json.loads(line)['text']
            torch.manual_seed(1234);random.seed(1234);np.random.seed(1234)
            model.eval()
            encoding=tokenizer(text,add_special_tokens=False,return_offsets_mapping=True)
            tokens=tokenizer.convert_ids_to_tokens(encoding['input_ids'])
            with torch.inference_mode(),contextlib.redirect_stdout(sys.stderr):
                _,_,trees,_,breaks=model.TestingLoss([tokens],None,None,None,GenerateTree=True,use_pred_segmentation=True)
            spans=[];start=0
            for end in breaks[0]:
                a,b=encoding['offset_mapping'][start][0],encoding['offset_mapping'][end][1]
                spans.append({'id':len(spans)+1,'span':[a,b],'text':text[a:b]});start=end+1
            tree=[]
            pattern=r'\((\d+):(Nucleus|Satellite)=([^:]+):(\d+),(\d+):(Nucleus|Satellite)=([^:]+):(\d+)\)'
            for fragment in trees[0]:
                for match in re.finditer(pattern,fragment):
                    a,n1,r1,b,c,n2,r2,d=match.groups()
                    tree.append({'left':[int(a),int(b)],'right':[int(c),int(d)],'left_nuclearity':n1,'right_nuclearity':n2,'relation':r1 if r1!='span' else r2})
            result={'status':'ready','backend':'DMRST_cpu','checkpoint_sha256':digest,'edus':spans,'tree':tree}
        except Exception as exc:
            result={'status':'unavailable','reason':type(exc).__name__,'edus':[],'tree':[]}
        print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
