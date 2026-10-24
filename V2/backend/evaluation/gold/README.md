# Sanctuary V2 Gold Annotation Dataset Split

## Split Overview
- **Development Set**: `dev_80_annotated.json` (80 turns from historical audit dataset, used for tuning).
- **Annotator 2 Verification**: `annotator2_dev20.json` (20 turns, 25% sample for Cohen's kappa agreement calculation).
- **Held-Out Test Set**: `held_out_test_40.json` (40 fresh turns, >=50% hard negatives, frozen).
- **Frozen Test Set Hash (SHA-256)**: `5b8d77a415c1a71c69183616a2ca85ea9e809e4653b1dda403f661908d4f0dbd` (recorded in `TEST_HASH.txt`).

## Hard Negative Catalogue Coverage in Held-Out Test Set
The held-out test set explicitly includes the following hard-negative classes:
1. **Causal**:
   - Zero-edge juxtaposition (`test_01_causal_juxtaposition`)
   - Non-clausal "because of" noun phrase (`test_02_causal_because_of_noun`)
   - Ambiguous temporal "since" (`test_03_causal_since_temporal`)
   - Anaphoric causal "that's why" (`test_04_causal_thats_why`)
   - Relative causal "which is why" (`test_05_causal_which_is_why`)
   - Verbal causative "led to" (`test_06_causal_led_to`)
   - Verbal causative "made me" (`test_07_causal_made_me`)
2. **Contrast**:
   - Idiomatic "nothing but" non-contrast (`test_08_contrast_nothing_but`)
   - Idiomatic "all but" non-contrast (`test_09_contrast_all_but`)
   - Sentence-final "though" (`test_10_contrast_final_though`)
3. **Negation**:
   - Discourse marker "never mind" (`test_11_negation_never_mind`)
   - Additive coordination "not only X but also Y" (`test_12_negation_not_only_but_also`)
   - Negation raising "I don't think I am angry" (`test_13_negation_raising`)
   - Quantifier negation "no one" (`test_14_negation_no_one`)
   - Idiomatic affirmative "can't help but" (`test_15_negation_cant_help_but`)
   - Double negation litotes "not unhappy" (`test_16_negation_double_litotes`)
4. **Roles**:
   - Passive voice recovery (`test_17_roles_passive_recovery`)
   - Third-party reporting "she told me he was wrong" (`test_18_roles_she_told_me`)
   - Direct reporting "I told her he was wrong" (`test_19_roles_i_told_her`)
5. **Corrections**:
   - Explicit repair "no wait, I meant" (`test_20_corrections_explicit_repair`)
   - Conversational refusal vs epistemic correction (`test_21_corrections_conversational_refusal`)
   - Filler / booster "actually" (`test_22_corrections_filler_actually`)
   - Non-nearest predicate target (`test_23_corrections_non_nearest_target`)
6. **References**:
   - Ambiguous gendered pronoun ("she") with two eligible antecedents (`test_24_references_ambiguous_pronoun`)
   - Pronoun with zero nominal antecedent in discourse ("they") (`test_25_references_no_antecedent`)
7. **Entities**:
   - Name inside quoted speech (`test_26_entities_name_inside_quote`)
   - Lowercase Indian proper names and stations (`test_27_entities_lowercase_names`)
   - User typing literal placeholder string (`test_28_entities_literal_placeholder`)
   - Common noun collision: "Joy" (`test_29_entities_common_noun_joy`)
   - Common noun collision: "Summer" (`test_30_entities_common_noun_summer`)
8. **Open-Vocabulary Non-Affective Turns**:
   - Logistics without emotion: Chembur flat deposit (`test_31_open_vocab_neutral_logistics`)
   - Pure factual narration with zero discourse gaps (`test_32_open_vocab_factual_narration`)
   - Humor / sarcasm (`test_33_open_vocab_humor_sarcasm`)
   - Good news and excitement (`test_34_open_vocab_good_news`)
   - Stated complete plan (`test_35_open_vocab_stated_plan`)
   - Venting with explicit request to not be questioned (`test_36_open_vocab_venting_no_questions`)
   - Short turns: "ok", "hm" (`test_37`, `test_38`)
   - Mumbai Hinglish code-mixing (`test_39_open_vocab_code_mixed_hinglish`)
   - Explicit hold request (`test_40_open_vocab_explicit_hold`)

## Freezing Protocol
The held-out test set `held_out_test_40.json` is strictly frozen and must remain untouched until Phase 6 evaluation.
