"""Fast unit tests (no data files needed):  python -m pytest -q"""
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import ModelConfig  # noqa: E402
from src.data_cleaning import clean_text  # noqa: E402
from src.data_loader import parse_type_path  # noqa: E402
from src.evaluation import corpus_bleu, rouge_scores, sentence_bleu  # noqa: E402
from src.inference import beam_search, greedy_decode  # noqa: E402
from src.preprocessing import detokenize, serialize_event, tokenize, truncate_at_sentence  # noqa: E402
from src.seq2seq import build_model  # noqa: E402
from src.vocabulary import EOS_IDX, PAD_IDX, SOS_IDX, UNK_IDX, Vocabulary  # noqa: E402


def test_tokenize_french():
    assert tokenize("L'atelier d'aujourd'hui : 14h30 !") == ["l'", "atelier", "d'", "aujourd'hui", ":", "14h30", "!"]
    assert tokenize("Vide-grenier, 2,5 €.") == ["vide-grenier", ",", "2,5", "€", "."]


def test_detokenize_roundtrip_readable():
    s = detokenize(tokenize("Venez découvrir l'exposition. Entrée libre !"))
    assert s == "Venez découvrir l'exposition. Entrée libre !"


def test_clean_text_removes_noise():
    t = clean_text("<p>Infos : www.site.fr ou 06 12 34 56 78 / a@b.fr</p>   BROUN\\u00cfAK!!!")
    assert "www" not in t and "06" not in t and "@" not in t and "<p>" not in t
    assert "BROUNÏAK!" in t


def test_type_parsing():
    assert parse_type_path("schema:Event/schema:MusicEvent/Concert/CulturalEvent/EntertainmentAndEvent/"
                           "PointOfInterest/urn:resource")[:2] == ["musique", "concert"]
    assert parse_type_path("u/r/n/:/r/e/s/o/u/r/c/e") == []
    assert serialize_event("Fête", []) == "type : non précisé | titre : Fête"


def test_truncate_at_sentence():
    toks = tokenize("Un deux trois. Quatre cinq six sept")
    assert truncate_at_sentence(toks, 6) == ["un", "deux", "trois", "."]
    assert truncate_at_sentence(["a"] * 10, 5) is None


def test_vocabulary_special_tokens_and_unk():
    v = Vocabulary(min_freq=1).build([["a", "b", "a"]])
    assert v.idx2word[:4] == ["<pad>", "<unk>", "<sos>", "<eos>"]
    ids = v.encode(["a", "zzz"], add_sos_eos=True)
    assert ids[0] == SOS_IDX and ids[-1] == EOS_IDX and ids[2] == UNK_IDX
    assert v.decode(ids) == ["a", "<unk>"]


def test_metrics_sanity():
    ref = tokenize("le marché de noël ouvre ses portes samedi matin .")
    assert abs(corpus_bleu([ref], [ref])["bleu"] - 100) < 1e-6
    assert rouge_scores(ref, ref)["rougeL"] == 1.0
    assert sentence_bleu([], ref) == 0.0


def _batch():
    src = torch.tensor([[5, 6, 7, 8], [5, 6, PAD_IDX, PAD_IDX]])
    src_len = torch.tensor([4, 2])
    tgt = torch.tensor([[SOS_IDX, 9, 10, EOS_IDX], [SOS_IDX, 11, EOS_IDX, PAD_IDX]])
    return src, src_len, tgt


def test_models_shapes_and_masking():
    for kind in ("baseline", "attention"):
        m = build_model(ModelConfig(model_type=kind, emb_dim=16, hid_dim=32, attn_dim=16), 20, 30).eval()
        src, src_len, tgt = _batch()
        logits, attn = m(src, src_len, tgt, teacher_forcing=1.0, return_attention=True)
        assert logits.shape == (2, 3, 30)
        if kind == "attention":
            assert attn.shape == (2, 3, 4)
            assert torch.allclose(attn.sum(-1), torch.ones(2, 3), atol=1e-5)
            assert attn[1, :, 2:].abs().max() == 0          # no attention on <pad>
        outs, _ = greedy_decode(m, src, src_len, max_len=5)
        assert len(outs) == 2 and all(UNK_IDX not in o for o in outs)
        ids, _, _ = beam_search(m, src[:1], src_len[:1], beam_width=3, max_len=5)
        assert isinstance(ids, list) and UNK_IDX not in ids
