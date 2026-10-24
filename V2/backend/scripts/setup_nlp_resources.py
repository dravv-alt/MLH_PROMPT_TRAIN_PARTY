"""Explicit resource setup; no runtime network downloads during text analysis."""
import argparse
from pathlib import Path


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dmrst',action='store_true');parser.add_argument('--backbone-only',action='store_true');args=parser.parse_args()
    import nltk
    import benepar
    cache=Path(__file__).resolve().parents[1]/'models/nltk'
    cache.mkdir(parents=True,exist_ok=True)
    nltk.data.path.insert(0,str(cache))
    nltk.download('wordnet',download_dir=str(cache),raise_on_error=True)
    benepar.download('benepar_en3',download_dir=str(cache))
    if args.dmrst or args.backbone_only:
        import gdown
        from huggingface_hub import snapshot_download
        root=Path(__file__).resolve().parents[1]/'models/dmrst';root.mkdir(parents=True,exist_ok=True)
        checkpoint=root/'multi_all_checkpoint.torchsave'
        if not args.backbone_only and not checkpoint.exists():
            gdown.download(id='12Gc6mC6Qh0R_N_U60mx2jDQqRfuwQzZh',output=str(checkpoint),quiet=False)
        if not args.backbone_only and (not checkpoint.exists() or checkpoint.stat().st_size<1000000):
            raise RuntimeError('Official DMRST checkpoint download did not complete')
        snapshot_download('FacebookAI/xlm-roberta-base',local_dir=str(root/'xlm-roberta-base'),allow_patterns=['config.json','model.safetensors','tokenizer.json','tokenizer_config.json','sentencepiece.bpe.model'])


if __name__=='__main__':main()
