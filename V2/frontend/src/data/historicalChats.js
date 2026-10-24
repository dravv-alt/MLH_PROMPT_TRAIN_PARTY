/**
 * Historical Chats and Memories derived from the Sanctuary V2 80-Turn Evaluation Dataset.
 * Every dialogue output is written in Sanctuary's natural contemplative reflective voice.
 * Generated dynamically via the client-side NLP Engine (PII distillation, clause parsing, Centering traces).
 */

export const HISTORICAL_CHATS = [
  {
    "id": "chat-achievement",
    "topic_id": "achievement_exhaustion_and_the_meaning_of_success",
    "title": "Achievement, exhaustion and the meaning of success",
    "date": "Yesterday · 09:14 AM",
    "time": "09:14",
    "preview": "I finally got the internship I've been working toward for months. Everyone's congratulating me, and I know I should be happy...",
    "tags": [
      "Achievement",
      "Pacing",
      "Rest"
    ],
    "messages": [
      {
        "role": "user",
        "time": "09:14",
        "rawText": "I finally got the internship I've been working toward for months. Everyone's congratulating me, and I know I should be happy. But honestly, I just feel tired. Now I'm already thinking about what I need to achieve next.",
        "text": "I finally got the internship I've been working toward for months. Everyone's congratulating me, and I know I should be happy. But honestly, I just feel tired. Now I'm already thinking about what I need to achieve next.",
        "turnData": {
          "rawText": "I finally got the internship I've been working toward for months. Everyone's congratulating me, and I know I should be happy. But honestly, I just feel tired. Now I'm already thinking about what I need to achieve next.",
          "maskedText": "I finally got the internship I've been working toward for months. Everyone's congratulating me, and I know I should be happy. But honestly, I just feel tired. Now I'm already thinking about what I need to achieve next.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I finally got the internship I've been working toward for months.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Everyone's congratulating me, and I know I should be happy.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "But honestly, I just feel tired.",
              "sentence": 2
            },
            {
              "id": "Clause D",
              "text": "Now I'm already thinking about what I need to achieve next.",
              "sentence": 3
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "speaker:self",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            },
            {
              "term": "speaker:self",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I finally got the internship I've been working toward for months.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "Everyone's congratulating me, and I know I should be happy.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            },
            {
              "sentence": 2,
              "sentenceText": "But honestly, I just feel tired.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "CONTINUE",
              "cost": 0
            },
            {
              "sentence": 3,
              "sentenceText": "Now I'm already thinking about what I need to achieve next.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "CONTINUE",
              "cost": 0
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "09:15",
        "paragraphs": [
          "The finish line arrived, but the momentum didn't know how to stop. Sometimes exhaustion is not a failure of joy—it is simply the body acknowledging how far it ran to get here. What would happen if the next goal waited until the tiredness had its say?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "The finish line arrived, but the momentum didn't know how to stop. Sometimes exhaustion is not a failure of joy—it is simply the body acknowledging how far it ran to get here. What would happen if the next goal waited until the tiredness had its say?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The finish line arrived,",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "the momentum didn't know how to stop.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "Sometimes exhaustion is not a failure of joy—it is simply the body acknowledging how far it ran to get here.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "What would happen",
              "sentence": 2
            },
            {
              "id": "Clause E",
              "text": "the next goal waited until the tiredness had its say?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "but",
              "type": "Pivot / Counter-condition",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            },
            {
              "id": "rel_2",
              "cue": "if",
              "type": "Condition / Premise",
              "source": "Clause D",
              "target": "Clause E",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "09:17",
        "rawText": "I don't think the tiredness is necessarily from the internship itself. I think I'm exhausted by the feeling that I have to keep proving I'm worth the opportunity.",
        "text": "I don't think the tiredness is necessarily from the internship itself. I think I'm exhausted by the feeling that I have to keep proving I'm worth the opportunity.",
        "turnData": {
          "rawText": "I don't think the tiredness is necessarily from the internship itself. I think I'm exhausted by the feeling that I have to keep proving I'm worth the opportunity.",
          "maskedText": "I don't think the tiredness is necessarily from the internship itself. I think I'm exhausted by the feeling that I have to keep proving I'm worth the opportunity.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I don't think the tiredness is necessarily from the internship itself.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I think I'm exhausted by the feeling that I have to keep proving I'm worth the opportunity.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I don't think the tiredness is necessarily from the internship itself.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I think I'm exhausted by the feeling that I have to keep proving I'm worth the opportunity.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "09:18",
        "paragraphs": [
          "The burden shifted from the work itself to the quiet demand of having to justify your seat. Carrying the need to prove your worth takes its own steady toll. Does that pressure feel like something external, or a voice you brought with you?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "The burden shifted from the work itself to the quiet demand of having to justify your seat. Carrying the need to prove your worth takes its own steady toll. Does that pressure feel like something external, or a voice you brought with you?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The burden shifted from the work itself to the quiet demand of having to justify your seat.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Carrying the need to prove your worth takes its own steady toll.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "Does that pressure feel like something external, or a voice you brought with you?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "09:20",
        "rawText": "Actually, I don't think I need to prove that I'm worthy. I'm excited about the internship. I'm just physically exhausted after months of preparation, and I want to enjoy the achievement without immediately planning the next thing.",
        "text": "Actually, I don't think I need to prove that I'm worthy. I'm excited about the internship. I'm just physically exhausted after months of preparation, and I want to enjoy the achievement without immediately planning the next thing.",
        "turnData": {
          "rawText": "Actually, I don't think I need to prove that I'm worthy. I'm excited about the internship. I'm just physically exhausted after months of preparation, and I want to enjoy the achievement without immediately planning the next thing.",
          "maskedText": "Actually, I don't think I need to prove that I'm worthy. I'm excited about the internship. I'm just physically exhausted after months of preparation, and I want to enjoy the achievement without immediately planning the next thing.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Actually, I don't think I need to prove that I'm worthy.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I'm excited about the internship.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "I'm just physically exhausted after months of preparation, and I want to enjoy the achievement without immediately planning the next thing.",
              "sentence": 2
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "speaker:self",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Actually, I don't think I need to prove that I'm worthy.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I'm excited about the internship.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            },
            {
              "sentence": 2,
              "sentenceText": "I'm just physically exhausted after months of preparation, and I want to enjoy the achievement without immediately planning the next thing.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "CONTINUE",
              "cost": 0
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "09:21",
        "paragraphs": [
          "That is a vital distinction to honor. The fatigue is physical, earned through honest preparation, rather than an unfulfilled demand for worth. When you set aside the next plan, what does the excitement feel like right now in your body?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "That is a vital distinction to honor. The fatigue is physical, earned through honest preparation, rather than an unfulfilled demand for worth. When you set aside the next plan, what does the excitement feel like right now in your body?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That is a vital distinction to honor.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "The fatigue is physical, earned through honest preparation, rather than an unfulfilled demand for worth.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "When you set aside the next plan, what does the excitement feel like right now in your body?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "09:23",
        "rawText": "I think I've spent so long preparing for this that I don't really know how to stop preparing. Even when something goes right, part of me is already looking for the next task.",
        "text": "I think I've spent so long preparing for this that I don't really know how to stop preparing. Even when something goes right, part of me is already looking for the next task.",
        "turnData": {
          "rawText": "I think I've spent so long preparing for this that I don't really know how to stop preparing. Even when something goes right, part of me is already looking for the next task.",
          "maskedText": "I think I've spent so long preparing for this that I don't really know how to stop preparing. Even when something goes right, part of me is already looking for the next task.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I think I've spent",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "long preparing for this that I don't really know how to stop preparing.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "Even",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "something goes right, part of me is already looking for the next task.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "so",
              "type": "Result / Consequence",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            },
            {
              "id": "rel_2",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I think I've spent so long preparing for this that I don't really know how to stop preparing.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "Even when something goes right, part of me is already looking for the next task.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "09:24",
        "paragraphs": [
          "Preparation became an involuntary rhythm, outlasting the need that originally set it in motion. When vigilance has kept you safe or successful for months, resting feels unfamiliar. Where do you notice the urge to brace for the next task?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "Preparation became an involuntary rhythm, outlasting the need that originally set it in motion. When vigilance has kept you safe or successful for months, resting feels unfamiliar. Where do you notice the urge to brace for the next task?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "Preparation became an involuntary rhythm, outlasting the need that originally set it in motion.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "When vigilance has kept you safe or successful for months, resting feels unfamiliar.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "Where do you notice the urge to brace for the next task?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "09:26",
        "rawText": "Although, I did enjoy telling my closest friend about it yesterday. I wasn't thinking about my next goal then.",
        "text": "Although, I did enjoy telling my closest friend about it yesterday. I wasn't thinking about my next goal then.",
        "turnData": {
          "rawText": "Although, I did enjoy telling my closest friend about it yesterday. I wasn't thinking about my next goal then.",
          "maskedText": "Although, I did enjoy telling my closest friend about it yesterday. I wasn't thinking about my next goal then.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Although, I did enjoy telling my closest friend about it yesterday.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I wasn't thinking about my next goal then.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Although, I did enjoy telling my closest friend about it yesterday.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I wasn't thinking about my next goal then.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 0,
              "tokenIndex": 9,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "09:27",
        "paragraphs": [
          "In shared warmth, the habit of measuring future tasks quietly slipped away. The capacity to be present with the good news is already here when the air feels safe. What made that conversation feel different from the surrounding noise?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "In shared warmth, the habit of measuring future tasks quietly slipped away. The capacity to be present with the good news is already here when the air feels safe. What made that conversation feel different from the surrounding noise?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "In shared warmth, the habit of measuring future tasks quietly slipped away.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "The capacity to be present with the good news is already here",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "the air feels safe.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "What made that conversation feel different from the surrounding noise?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "09:29",
        "rawText": "Maybe I don't need to stop thinking about the future completely. I just don't want every good thing to turn into another deadline.",
        "text": "Maybe I don't need to stop thinking about the future completely. I just don't want every good thing to turn into another deadline.",
        "turnData": {
          "rawText": "Maybe I don't need to stop thinking about the future completely. I just don't want every good thing to turn into another deadline.",
          "maskedText": "Maybe I don't need to stop thinking about the future completely. I just don't want every good thing to turn into another deadline.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Maybe I don't need to stop thinking about the future completely.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I just don't want every good thing to turn into another deadline.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Maybe I don't need to stop thinking about the future completely.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I just don't want every good thing to turn into another deadline.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "09:30",
        "paragraphs": [
          "Looking ahead doesn't have to carry the weight of a countdown. You are carving out space where anticipation can exist without hardening into obligation. How does a milestone feel when it isn't treated as a deadline?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "Looking ahead doesn't have to carry the weight of a countdown. You are carving out space where anticipation can exist without hardening into obligation. How does a milestone feel when it isn't treated as a deadline?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "Looking ahead doesn't have to carry the weight of a countdown.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "You are carving out space where anticipation can exist without hardening into obligation.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "How does a milestone feel",
              "sentence": 2
            },
            {
              "id": "Clause D",
              "text": "it isn't treated as a deadline?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": []
        }
      },
      {
        "role": "user",
        "time": "09:32",
        "rawText": "My manager also said I don't need to know everything immediately. That was reassuring, even though I still want to do well.",
        "text": "My manager also said I don't need to know everything immediately. That was reassuring, even though I still want to do well.",
        "turnData": {
          "rawText": "My manager also said I don't need to know everything immediately. That was reassuring, even though I still want to do well.",
          "maskedText": "My manager also said I don't need to know everything immediately. That was reassuring, even though I still want to do well.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "My manager also said I don't need to know everything immediately.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "That was reassuring,",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "I still want to do well.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "even though",
              "type": "Contrast / Exception",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": true
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "My manager also said I don't need to know everything immediately.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "That was reassuring, even though I still want to do well.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "09:33",
        "paragraphs": [
          "Permission to arrive as a learner was offered, and some of the perimeter softened. You can hold both things without contradiction: an earnest desire to excel, and permission to start from where you are. Does hearing that give your shoulders a moment to drop?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "Permission to arrive as a learner was offered, and some of the perimeter softened. You can hold both things without contradiction: an earnest desire to excel, and permission to start from where you are. Does hearing that give your shoulders a moment to drop?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "Permission to arrive as a learner was offered, and some of the perimeter softened.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "You can hold both things without contradiction: an earnest desire to excel, and permission to start from where you are.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "Does hearing that give your shoulders a moment to drop?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": []
        }
      },
      {
        "role": "user",
        "time": "09:35",
        "rawText": "I noticed I felt better after I slept properly. That makes me think the physical exhaustion was a bigger part of this than I first realized.",
        "text": "I noticed I felt better after I slept properly. That makes me think the physical exhaustion was a bigger part of this than I first realized.",
        "turnData": {
          "rawText": "I noticed I felt better after I slept properly. That makes me think the physical exhaustion was a bigger part of this than I first realized.",
          "maskedText": "I noticed I felt better after I slept properly. That makes me think the physical exhaustion was a bigger part of this than I first realized.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I noticed I felt better after I slept properly.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "That makes me think the physical exhaustion was a bigger part of this than I first realized.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I noticed I felt better after I slept properly.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "That makes me think the physical exhaustion was a bigger part of this than I first realized.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "09:36",
        "paragraphs": [
          "A full night's rest restored what narrative analysis couldn't touch. Sometimes the mind invents complicated explanations for what is simply somatic depletion asking for sleep. How does the accomplishment look today with more rested eyes?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "A full night's rest restored what narrative analysis couldn't touch. Sometimes the mind invents complicated explanations for what is simply somatic depletion asking for sleep. How does the accomplishment look today with more rested eyes?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "A full night's rest restored what narrative analysis couldn't touch.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Sometimes the mind invents complicated explanations for what is simply somatic depletion asking for sleep.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "How does the accomplishment look today with more rested eyes?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "09:38",
        "rawText": "I'm still thinking about what comes next, but it doesn't feel as urgent today. I can be excited and tired at the same time.",
        "text": "I'm still thinking about what comes next, but it doesn't feel as urgent today. I can be excited and tired at the same time.",
        "turnData": {
          "rawText": "I'm still thinking about what comes next, but it doesn't feel as urgent today. I can be excited and tired at the same time.",
          "maskedText": "I'm still thinking about what comes next, but it doesn't feel as urgent today. I can be excited and tired at the same time.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I'm still thinking about what comes next,",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "it doesn't feel as urgent today.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "I can be excited and tired at the same time.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "but",
              "type": "Pivot / Counter-condition",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I'm still thinking about what comes next, but it doesn't feel as urgent today.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I can be excited and tired at the same time.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 0,
              "tokenIndex": 8,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "09:39",
        "paragraphs": [
          "The urgency softened into something you can walk alongside rather than obey. Allowing excitement and fatigue to sit together without demanding a verdict creates real room to breathe. What does it feel like to let both be true?"
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "The urgency softened into something you can walk alongside rather than obey. Allowing excitement and fatigue to sit together without demanding a verdict creates real room to breathe. What does it feel like to let both be true?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The urgency softened into something you can walk alongside rather than obey.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Allowing excitement and fatigue to sit together without demanding a verdict creates real room to breathe.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What does it feel like to let both be true?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "09:41",
        "rawText": "If I had to describe the whole thing now, I'd say I'm proud of what I achieved, physically tired from getting here, and trying to give myself room to enjoy it before moving on.",
        "text": "If I had to describe the whole thing now, I'd say I'm proud of what I achieved, physically tired from getting here, and trying to give myself room to enjoy it before moving on.",
        "turnData": {
          "rawText": "If I had to describe the whole thing now, I'd say I'm proud of what I achieved, physically tired from getting here, and trying to give myself room to enjoy it before moving on.",
          "maskedText": "If I had to describe the whole thing now, I'd say I'm proud of what I achieved, physically tired from getting here, and trying to give myself room to enjoy it before moving on.",
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "If I had to describe the whole thing now, I'd say I'm proud of what I achieved, physically tired from getting here, and trying to give myself room to enjoy it before moving on.",
              "sentence": 0
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "If I had to describe the whole thing now, I'd say I'm proud of what I achieved, physically tired from getting here, and trying to give myself room to enjoy it before moving on.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 0,
              "tokenIndex": 30,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "09:42",
        "paragraphs": [
          "That holds the whole truth of it: the hard-won pride, the honest tiredness of the journey, and the patience to dwell in the clearing before walking on. That is not stagnation—it is receiving what you worked so hard to create."
        ],
        "turnData": {
          "entity": "[Achievement]",
          "entityType": "Local RAM Session",
          "maskedText": "That holds the whole truth of it: the hard-won pride, the honest tiredness of the journey, and the patience to dwell in the clearing before walking on. That is not stagnation—it is receiving what you worked so hard to create.",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That holds the whole truth of it: the hard-won pride, the honest tiredness of the journey, and the patience to dwell in the clearing before walking on.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "That is not stagnation—it is receiving what you worked",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "hard to create.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "so",
              "type": "Result / Consequence",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": []
        }
      }
    ]
  },
  {
    "id": "chat-pattern",
    "topic_id": "the_recurring_pattern",
    "title": "The recurring pattern of planning",
    "date": "2 days ago · 02:40 PM",
    "time": "14:40",
    "preview": "I've noticed that whenever I start something important, I make a very detailed plan before I actually begin...",
    "tags": [
      "Planning",
      "Observation",
      "Action"
    ],
    "messages": [
      {
        "role": "user",
        "time": "14:40",
        "rawText": "I've noticed that whenever I start something important, I make a very detailed plan before I actually begin.",
        "text": "I've noticed that whenever I start something important, I make a very detailed plan before I actually begin.",
        "turnData": {
          "rawText": "I've noticed that whenever I start something important, I make a very detailed plan before I actually begin.",
          "maskedText": "I've noticed that whenever I start something important, I make a very detailed plan before I actually begin.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I've noticed that whenever I start something important, I make a very detailed plan before I actually begin.",
              "sentence": 0
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I've noticed that whenever I start something important, I make a very detailed plan before I actually begin.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "14:41",
        "paragraphs": [
          "The map is drawn before the first footstep is placed on the road. Building the structure provides a quiet territory where the outcome feels held. What does putting together that outline feel like right at the start?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "The map is drawn before the first footstep is placed on the road. Building the structure provides a quiet territory where the outcome feels held. What does putting together that outline feel like right at the start?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The map is drawn before the first footstep is placed on the road.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Building the structure provides a quiet territory where the outcome feels held.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What does putting together that outline feel like right at the start?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "14:43",
        "rawText": "It happened with my last assignment too. I spent almost two evenings organizing everything before writing the first paragraph.",
        "text": "It happened with my last assignment too. I spent almost two evenings organizing everything before writing the first paragraph.",
        "turnData": {
          "rawText": "It happened with my last assignment too. I spent almost two evenings organizing everything before writing the first paragraph.",
          "maskedText": "It happened with my last assignment too. I spent almost two evenings organizing everything before writing the first paragraph.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "It happened with my last assignment too.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I spent almost two evenings organizing everything before writing the first paragraph.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "It happened with my last assignment too.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I spent almost two evenings organizing everything before writing the first paragraph.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 0,
              "tokenIndex": 0,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "14:44",
        "paragraphs": [
          "Two evenings spent arranging the architecture before confronting the blank page. The boundary between organizing and starting can blur so softly that it feels like progress. What felt more hospitable about organizing than beginning?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "Two evenings spent arranging the architecture before confronting the blank page. The boundary between organizing and starting can blur so softly that it feels like progress. What felt more hospitable about organizing than beginning?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "Two evenings spent arranging the architecture before confronting the blank page.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "The boundary between organizing and starting can blur",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "softly that it feels like progress.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "What felt more hospitable about organizing than beginning?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "so",
              "type": "Result / Consequence",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "14:46",
        "rawText": "I guess I do this because I'm afraid of doing things badly.",
        "text": "I guess I do this because I'm afraid of doing things badly.",
        "turnData": {
          "rawText": "I guess I do this because I'm afraid of doing things badly.",
          "maskedText": "I guess I do this because I'm afraid of doing things badly.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I guess I do this",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I'm afraid of doing things badly.",
              "sentence": 0
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I guess I do this because I'm afraid of doing things badly.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "14:47",
        "paragraphs": [
          "A thorough plan can become a shield against the vulnerability of an imperfect beginning. If every detail is arranged beforehand, the risk of misstepping feels contained. Does that fear feel sharp, or more like a quiet background pressure?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "A thorough plan can become a shield against the vulnerability of an imperfect beginning. If every detail is arranged beforehand, the risk of misstepping feels contained. Does that fear feel sharp, or more like a quiet background pressure?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "A thorough plan can become a shield against the vulnerability of an imperfect beginning.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "If every detail is arranged beforehand, the risk of misstepping feels contained.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "Does that fear feel sharp, or more like a quiet background pressure?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "14:49",
        "rawText": "Actually, that isn't always it. Sometimes I plan because I genuinely enjoy organizing a complicated problem.",
        "text": "Actually, that isn't always it. Sometimes I plan because I genuinely enjoy organizing a complicated problem.",
        "turnData": {
          "rawText": "Actually, that isn't always it. Sometimes I plan because I genuinely enjoy organizing a complicated problem.",
          "maskedText": "Actually, that isn't always it. Sometimes I plan because I genuinely enjoy organizing a complicated problem.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Actually, that isn't always it.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Sometimes I plan",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "I genuinely enjoy organizing a complicated problem.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Actually, that isn't always it.",
              "cf": [
                "contemplative_presence"
              ],
              "cp": "contemplative_presence",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "Sometimes I plan because I genuinely enjoy organizing a complicated problem.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 0,
              "tokenIndex": 4,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "14:50",
        "paragraphs": [
          "That is a real distinction to preserve. Bringing order to an intricate problem carries its own craftsmanship and pleasure, entirely separate from fear. When you're lost in that enjoyment, how does it feel compared to the urge to avoid?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "That is a real distinction to preserve. Bringing order to an intricate problem carries its own craftsmanship and pleasure, entirely separate from fear. When you're lost in that enjoyment, how does it feel compared to the urge to avoid?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That is a real distinction to preserve.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Bringing order to an intricate problem carries its own craftsmanship and pleasure, entirely separate from fear.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "When you're lost in that enjoyment, how does it feel compared to the urge to avoid?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "14:52",
        "rawText": "With the assignment, though, I was definitely avoiding the writing. I kept finding more things to organize instead.",
        "text": "With the assignment, though, I was definitely avoiding the writing. I kept finding more things to organize instead.",
        "turnData": {
          "rawText": "With the assignment, though, I was definitely avoiding the writing. I kept finding more things to organize instead.",
          "maskedText": "With the assignment, though, I was definitely avoiding the writing. I kept finding more things to organize instead.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "With the assignment, though, I was definitely avoiding the writing.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I kept finding more things to organize instead.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "With the assignment, though, I was definitely avoiding the writing.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I kept finding more things to organize instead.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "14:53",
        "paragraphs": [
          "In that specific moment, the organizing expanded to hold back the blank screen. When a task carries an evaluation, rearranging the tools feels safer than applying them to the stone. What was it about writing that first sentence that felt heavy?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "In that specific moment, the organizing expanded to hold back the blank screen. When a task carries an evaluation, rearranging the tools feels safer than applying them to the stone. What was it about writing that first sentence that felt heavy?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "In that specific moment, the organizing expanded to hold back the blank screen.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "When a task carries an evaluation, rearranging the tools feels safer than applying them to the stone.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What was it about writing that first sentence that felt heavy?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "14:55",
        "rawText": "Last weekend I started a small coding project without a plan and actually enjoyed figuring it out as I went.",
        "text": "Last weekend I started a small coding project without a plan and actually enjoyed figuring it out as I went.",
        "turnData": {
          "rawText": "Last weekend I started a small coding project without a plan and actually enjoyed figuring it out as I went.",
          "maskedText": "Last weekend I started a small coding project without a plan and actually enjoyed figuring it out as I went.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Last weekend I started a small coding project without a plan and actually enjoyed figuring it out as I went.",
              "sentence": 0
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Last weekend I started a small coding project without a plan and actually enjoyed figuring it out as I went.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 0,
              "tokenIndex": 15,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "14:56",
        "paragraphs": [
          "Without an audience or a grade, you could wander directly into the material and let it take shape beneath your hands. The need for exhaustive preparation evaporated when the stakes belonged only to you. How did it feel to step into the dark without the map?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "Without an audience or a grade, you could wander directly into the material and let it take shape beneath your hands. The need for exhaustive preparation evaporated when the stakes belonged only to you. How did it feel to step into the dark without the map?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "Without an audience or a grade, you could wander directly into the material and let it take shape beneath your hands.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "The need for exhaustive preparation evaporated",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "the stakes belonged only to you.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "How did it feel to step into the dark without the map?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "14:58",
        "rawText": "The difference might be that the coding project didn't feel like anyone was going to judge the result.",
        "text": "The difference might be that the coding project didn't feel like anyone was going to judge the result.",
        "turnData": {
          "rawText": "The difference might be that the coding project didn't feel like anyone was going to judge the result.",
          "maskedText": "The difference might be that the coding project didn't feel like anyone was going to judge the result.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "The difference might be that the coding project didn't feel like anyone was going to judge the result.",
              "sentence": 0
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "The difference might be that the coding project didn't feel like anyone was going to judge the result.",
              "cf": [
                "contemplative_presence"
              ],
              "cp": "contemplative_presence",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "14:59",
        "paragraphs": [
          "The anticipated gaze of others is what tightens the requirements. When work is unobserved, beginning is an exploration; when judgment looms, beginning feels like exposure. Where do you first notice that expectation of judgment entering your thoughts?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "The anticipated gaze of others is what tightens the requirements. When work is unobserved, beginning is an exploration; when judgment looms, beginning feels like exposure. Where do you first notice that expectation of judgment entering your thoughts?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The anticipated gaze of others is what tightens the requirements.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "When work is unobserved, beginning is an exploration;",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "judgment looms, beginning feels like exposure.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "Where do you first notice that expectation of judgment entering your thoughts?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "15:01",
        "rawText": "I also realized that planning helps when the task is genuinely complicated. It becomes a problem when I keep planning after I already know enough to begin.",
        "text": "I also realized that planning helps when the task is genuinely complicated. It becomes a problem when I keep planning after I already know enough to begin.",
        "turnData": {
          "rawText": "I also realized that planning helps when the task is genuinely complicated. It becomes a problem when I keep planning after I already know enough to begin.",
          "maskedText": "I also realized that planning helps when the task is genuinely complicated. It becomes a problem when I keep planning after I already know enough to begin.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I also realized that planning helps",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "the task is genuinely complicated.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "It becomes a problem",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "I keep planning after I already know enough to begin.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            },
            {
              "id": "rel_2",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I also realized that planning helps when the task is genuinely complicated.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "It becomes a problem when I keep planning after I already know enough to begin.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 1,
              "tokenIndex": 1,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "15:02",
        "paragraphs": [
          "You've marked the exact threshold: between necessary cartography and continued hesitation disguised as preparation. Knowing that you already have enough to start is where courage quietly takes over from the plan. What tells you when that threshold has been crossed?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "You've marked the exact threshold: between necessary cartography and continued hesitation disguised as preparation. Knowing that you already have enough to start is where courage quietly takes over from the plan. What tells you when that threshold has been crossed?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "You've marked the exact threshold: between necessary cartography and continued hesitation disguised as preparation.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Knowing that you already have enough to start is where courage quietly takes over from the plan.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What tells you",
              "sentence": 2
            },
            {
              "id": "Clause D",
              "text": "that threshold has been crossed?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "15:04",
        "rawText": "Today I started the report after making only a rough outline. I still felt uncertain, but I could make progress.",
        "text": "Today I started the report after making only a rough outline. I still felt uncertain, but I could make progress.",
        "turnData": {
          "rawText": "Today I started the report after making only a rough outline. I still felt uncertain, but I could make progress.",
          "maskedText": "Today I started the report after making only a rough outline. I still felt uncertain, but I could make progress.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Today I started the report after making only a rough outline.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I still felt uncertain,",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "I could make progress.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "but",
              "type": "Pivot / Counter-condition",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Today I started the report after making only a rough outline.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I still felt uncertain, but I could make progress.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "15:05",
        "paragraphs": [
          "You stepped into the work with rough edges still showing, allowing uncertainty to accompany you rather than halt you. The first paragraph didn't need a finished guarantee to come alive. How did the draft look once words were actually on the page?"
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "You stepped into the work with rough edges still showing, allowing uncertainty to accompany you rather than halt you. The first paragraph didn't need a finished guarantee to come alive. How did the draft look once words were actually on the page?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "You stepped into the work with rough edges still showing, allowing uncertainty to accompany you rather than halt you.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "The first paragraph didn't need a finished guarantee to come alive.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "How did the draft look once words were actually on the page?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "15:07",
        "rawText": "So maybe the pattern isn't that I always procrastinate. It's that, with work I expect people to judge, I sometimes keep preparing after preparation has stopped helping.",
        "text": "So maybe the pattern isn't that I always procrastinate. It's that, with work I expect people to judge, I sometimes keep preparing after preparation has stopped helping.",
        "turnData": {
          "rawText": "So maybe the pattern isn't that I always procrastinate. It's that, with work I expect people to judge, I sometimes keep preparing after preparation has stopped helping.",
          "maskedText": "So maybe the pattern isn't that I always procrastinate. It's that, with work I expect people to judge, I sometimes keep preparing after preparation has stopped helping.",
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "So maybe the pattern isn't that I always procrastinate.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "It's that, with work I expect people to judge, I sometimes keep preparing after preparation has stopped helping.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "So maybe the pattern isn't that I always procrastinate.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "It's that, with work I expect people to judge, I sometimes keep preparing after preparation has stopped helping.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": [
            {
              "pronoun": "its",
              "sentenceIndex": 1,
              "tokenIndex": 1,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "15:08",
        "paragraphs": [
          "You've untangled an identity from a contextual response. You aren't someone who cannot begin; you are someone who notices when the instinct to buffer against judgment has lingered past its usefulness. That awareness itself is the boundary."
        ],
        "turnData": {
          "entity": "[Planning]",
          "entityType": "Local RAM Session",
          "maskedText": "You've untangled an identity from a contextual response. You aren't someone who cannot begin; you are someone who notices when the instinct to buffer against judgment has lingered past its usefulness. That awareness itself is the boundary.",
          "clauses": [
            {
              "id": "Clause A",
              "text": "You've untangled an identity from a contextual response.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "You aren't someone who cannot begin; you are someone who notices",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "the instinct to buffer against judgment has lingered past its usefulness.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "That awareness itself is the boundary.",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      }
    ]
  },
  {
    "id": "chat-resistance",
    "topic_id": "resistance_to_interpretation",
    "title": "Resistance to interpretation",
    "date": "4 days ago · 11:22 AM",
    "time": "11:22",
    "preview": "I've been quieter than usual around my friends lately. I don't really know why...",
    "tags": [
      "Stillness",
      "Autonomy",
      "Uncertainty"
    ],
    "messages": [
      {
        "role": "user",
        "time": "11:22",
        "rawText": "I've been quieter than usual around my friends lately. I don't really know why.",
        "text": "I've been quieter than usual around my friends lately. I don't really know why.",
        "turnData": {
          "rawText": "I've been quieter than usual around my friends lately. I don't really know why.",
          "maskedText": "I've been quieter than usual around my friends lately. I don't really know why.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I've been quieter than usual around my friends lately.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I don't really know why.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I've been quieter than usual around my friends lately.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I don't really know why.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "11:23",
        "paragraphs": [
          "A quietness settled in without announcing its reason or asking for permission. Sometimes speech steps back before the mind understands what asked it to recede. What does that silence feel like when you're sitting in the room?"
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "A quietness settled in without announcing its reason or asking for permission. Sometimes speech steps back before the mind understands what asked it to recede. What does that silence feel like when you're sitting in the room?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "A quietness settled in without announcing its reason or asking for permission.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Sometimes speech steps back before the mind understands what asked it to recede.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What does that silence feel like",
              "sentence": 2
            },
            {
              "id": "Clause D",
              "text": "you're sitting in the room?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:25",
        "rawText": "Maybe I'm upset with them, but I can't point to anything specific.",
        "text": "Maybe I'm upset with them, but I can't point to anything specific.",
        "turnData": {
          "rawText": "Maybe I'm upset with them, but I can't point to anything specific.",
          "maskedText": "Maybe I'm upset with them, but I can't point to anything specific.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Maybe I'm upset with them,",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I can't point to anything specific.",
              "sentence": 0
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "but",
              "type": "Pivot / Counter-condition",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Maybe I'm upset with them, but I can't point to anything specific.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "them",
              "sentenceIndex": 0,
              "tokenIndex": 4,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "11:26",
        "paragraphs": [
          "The mind reaches for grievance because conflict is easier to name than simple withdrawal. Yet without a concrete fracture, searching for resentment can feel like forcing a shape that isn't there. Does the quiet carry heat, or is it cooler than anger?"
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "The mind reaches for grievance because conflict is easier to name than simple withdrawal. Yet without a concrete fracture, searching for resentment can feel like forcing a shape that isn't there. Does the quiet carry heat, or is it cooler than anger?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The mind reaches for grievance",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "conflict is easier to name than simple withdrawal.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "Yet without a concrete fracture, searching for resentment can feel like forcing a shape that isn't there.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "Does the quiet carry heat, or is it cooler than anger?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:28",
        "rawText": "I did have a busy week, and by the time I meet them I sometimes don't have much energy left to talk.",
        "text": "I did have a busy week, and by the time I meet them I sometimes don't have much energy left to talk.",
        "turnData": {
          "rawText": "I did have a busy week, and by the time I meet them I sometimes don't have much energy left to talk.",
          "maskedText": "I did have a busy week, and by the time I meet them I sometimes don't have much energy left to talk.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I did have a busy week, and by the time I meet them I sometimes don't have much energy left to talk.",
              "sentence": 0
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I did have a busy week, and by the time I meet them I sometimes don't have much energy left to talk.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "them",
              "sentenceIndex": 0,
              "tokenIndex": 12,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "11:29",
        "paragraphs": [
          "The well had already been drawn down by the demands of the week before you ever sat across from them. A low battery doesn't require a psychological diagnosis to explain why words are scarce. How does it feel to simply let fatigue be fatigue?"
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "The well had already been drawn down by the demands of the week before you ever sat across from them. A low battery doesn't require a psychological diagnosis to explain why words are scarce. How does it feel to simply let fatigue be fatigue?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The well had already been drawn down by the demands of the week before you ever sat across from them.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "A low battery doesn't require a psychological diagnosis to explain why words are scarce.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "How does it feel to simply let fatigue be fatigue?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:31",
        "rawText": "I wonder if I'm pulling away because I'm afraid they'll notice I've changed.",
        "text": "I wonder if I'm pulling away because I'm afraid they'll notice I've changed.",
        "turnData": {
          "rawText": "I wonder if I'm pulling away because I'm afraid they'll notice I've changed.",
          "maskedText": "I wonder if I'm pulling away because I'm afraid they'll notice I've changed.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I wonder if I'm pulling away",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I'm afraid they'll notice I've changed.",
              "sentence": 0
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I wonder if I'm pulling away because I'm afraid they'll notice I've changed.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "11:32",
        "paragraphs": [
          "The possibility arises that retreating protects you from being seen in a state of flux. It is natural to wonder whether stepping back is a defense. But we don't have to turn that wondering into a final conclusion before you know."
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "The possibility arises that retreating protects you from being seen in a state of flux. It is natural to wonder whether stepping back is a defense. But we don't have to turn that wondering into a final conclusion before you know.",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The possibility arises that retreating protects you from being seen in a state of flux.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "It is natural to wonder whether stepping back is a defense.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "But we don't have to turn that wondering into a final conclusion before you know.",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:34",
        "rawText": "You keep making this sound like I'm afraid of something. I haven't said that it's fear. I'm trying to work out what's happening.",
        "text": "You keep making this sound like I'm afraid of something. I haven't said that it's fear. I'm trying to work out what's happening.",
        "turnData": {
          "rawText": "You keep making this sound like I'm afraid of something. I haven't said that it's fear. I'm trying to work out what's happening.",
          "maskedText": "You keep making this sound like I'm afraid of something. I haven't said that it's fear. I'm trying to work out what's happening.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "You keep making this sound like I'm afraid of something.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I haven't said that it's fear.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "I'm trying to work out what's happening.",
              "sentence": 2
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "speaker:self",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "You keep making this sound like I'm afraid of something.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I haven't said that it's fear.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            },
            {
              "sentence": 2,
              "sentenceText": "I'm trying to work out what's happening.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "CONTINUE",
              "cost": 0
            }
          ],
          "hobbsData": [
            {
              "pronoun": "its",
              "sentenceIndex": 1,
              "tokenIndex": 5,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "11:35",
        "paragraphs": [
          "I hear your correction clearly, and I step back from that framing. You haven't described fear, and putting that label on it only narrows the room you need to explore. Let's stay with what is actually present without borrowing words that don't fit."
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "I hear your correction clearly, and I step back from that framing. You haven't described fear, and putting that label on it only narrows the room you need to explore. Let's stay with what is actually present without borrowing words that don't fit.",
          "clauses": [
            {
              "id": "Clause A",
              "text": "I hear your correction clearly, and I step back from that framing.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "You haven't described fear, and putting that label on it only narrows the room you need to explore.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "Let's stay with what is actually present without borrowing words that don't fit.",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:37",
        "rawText": "I might be a little uncomfortable, but mostly I'm tired and less talkative. That's all I can confidently say right now.",
        "text": "I might be a little uncomfortable, but mostly I'm tired and less talkative. That's all I can confidently say right now.",
        "turnData": {
          "rawText": "I might be a little uncomfortable, but mostly I'm tired and less talkative. That's all I can confidently say right now.",
          "maskedText": "I might be a little uncomfortable, but mostly I'm tired and less talkative. That's all I can confidently say right now.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I might be a little uncomfortable,",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "mostly I'm tired and less talkative.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "That's all I can confidently say right now.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "but",
              "type": "Pivot / Counter-condition",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I might be a little uncomfortable, but mostly I'm tired and less talkative.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "That's all I can confidently say right now.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "11:38",
        "paragraphs": [
          "That is honest ground, and we will stay right there. Tiredness, a bit of discomfort, and a natural drop in words—nothing more needs to be assembled on top of that. Does holding just those three things feel lighter than building a theory?"
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "That is honest ground, and we will stay right there. Tiredness, a bit of discomfort, and a natural drop in words—nothing more needs to be assembled on top of that. Does holding just those three things feel lighter than building a theory?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That is honest ground, and we will stay right there.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Tiredness, a bit of discomfort, and a natural drop in words—nothing more needs to be assembled on top of that.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "Does holding just those three things feel lighter than building a theory?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:40",
        "rawText": "Yesterday I spent an entire evening with one friend and felt completely normal. It seems to happen more in groups.",
        "text": "Yesterday I spent an entire evening with one friend and felt completely normal. It seems to happen more in groups.",
        "turnData": {
          "rawText": "Yesterday I spent an entire evening with one friend and felt completely normal. It seems to happen more in groups.",
          "maskedText": "Yesterday I spent an entire evening with one friend and felt completely normal. It seems to happen more in groups.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Yesterday I spent an entire evening with one friend and felt completely normal.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "It seems to happen more in groups.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Yesterday I spent an entire evening with one friend and felt completely normal.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "It seems to happen more in groups.",
              "cf": [
                "contemplative_presence"
              ],
              "cp": "contemplative_presence",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 1,
              "tokenIndex": 1,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "11:41",
        "paragraphs": [
          "The quietness isn't a blanket withdrawal from connection; it is responsive to the scale of the room. One-on-one presence allowed your rhythm to settle, while the cross-currents of a group ask for a different kind of effort. What felt easier about that single conversation?"
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "The quietness isn't a blanket withdrawal from connection; it is responsive to the scale of the room. One-on-one presence allowed your rhythm to settle, while the cross-currents of a group ask for a different kind of effort. What felt easier about that single conversation?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The quietness isn't a blanket withdrawal from connection; it is responsive to the scale of the room.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "One-on-one presence allowed your rhythm to settle,",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "the cross-currents of a group ask for a different kind of effort.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "What felt easier about that single conversation?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "while",
              "type": "Temporal / Concession",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": true
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:43",
        "rawText": "Actually, one group conversation was fine too. I think it depends on the day and how much energy I have.",
        "text": "Actually, one group conversation was fine too. I think it depends on the day and how much energy I have.",
        "turnData": {
          "rawText": "Actually, one group conversation was fine too. I think it depends on the day and how much energy I have.",
          "maskedText": "Actually, one group conversation was fine too. I think it depends on the day and how much energy I have.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Actually, one group conversation was fine too.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I think it depends on the day and how much energy I have.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Actually, one group conversation was fine too.",
              "cf": [
                "contemplative_presence"
              ],
              "cp": "contemplative_presence",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I think it depends on the day and how much energy I have.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 1,
              "tokenIndex": 3,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "11:44",
        "paragraphs": [
          "Even the group distinction softens when looked at closely. It comes back to the immediate state of your energy on that particular day, fluctuating as human energy naturally does. Does giving yourself room to vary from day to day feel possible?"
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "Even the group distinction softens when looked at closely. It comes back to the immediate state of your energy on that particular day, fluctuating as human energy naturally does. Does giving yourself room to vary from day to day feel possible?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "Even the group distinction softens",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "looked at closely.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "It comes back to the immediate state of your energy on that particular day, fluctuating as human energy naturally does.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "Does giving yourself room to vary from day to day feel possible?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:46",
        "rawText": "I don't want to force an explanation just so the story makes sense. I'm okay with not knowing yet.",
        "text": "I don't want to force an explanation just so the story makes sense. I'm okay with not knowing yet.",
        "turnData": {
          "rawText": "I don't want to force an explanation just so the story makes sense. I'm okay with not knowing yet.",
          "maskedText": "I don't want to force an explanation just so the story makes sense. I'm okay with not knowing yet.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I don't want to force an explanation just",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "the story makes sense.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "I'm okay with not knowing yet.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "so",
              "type": "Result / Consequence",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I don't want to force an explanation just so the story makes sense.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I'm okay with not knowing yet.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "11:47",
        "paragraphs": [
          "There is deep sovereignty in refusing to tie a neat knot around an experience that is still living. Letting the unknown remain unknown without rushing to package it honors your real life. What opens up when the story is allowed to stay unfinished?"
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "There is deep sovereignty in refusing to tie a neat knot around an experience that is still living. Letting the unknown remain unknown without rushing to package it honors your real life. What opens up when the story is allowed to stay unfinished?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "There is deep sovereignty in refusing to tie a neat knot around an experience that is still living.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Letting the unknown remain unknown without rushing to package it honors your real life.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What opens up",
              "sentence": 2
            },
            {
              "id": "Clause D",
              "text": "the story is allowed to stay unfinished?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "11:49",
        "rawText": "For now, the most accurate description is that I've been quieter sometimes, especially when tired. I don't yet know whether there's a deeper reason.",
        "text": "For now, the most accurate description is that I've been quieter sometimes, especially when tired. I don't yet know whether there's a deeper reason.",
        "turnData": {
          "rawText": "For now, the most accurate description is that I've been quieter sometimes, especially when tired. I don't yet know whether there's a deeper reason.",
          "maskedText": "For now, the most accurate description is that I've been quieter sometimes, especially when tired. I don't yet know whether there's a deeper reason.",
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "For now, the most accurate description is that I've been quieter sometimes, especially",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "tired.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "I don't yet know whether there's a deeper reason.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "For now, the most accurate description is that I've been quieter sometimes, especially when tired.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I don't yet know whether there's a deeper reason.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "11:50",
        "paragraphs": [
          "That is the clearest and most truthful perimeter: you are quieter sometimes, especially when fatigue sets in, and whether anything more lies beneath can wait. No forced narrative, no unchosen labels—just reality resting at its own pace."
        ],
        "turnData": {
          "entity": "[Stillness]",
          "entityType": "Local RAM Session",
          "maskedText": "That is the clearest and most truthful perimeter: you are quieter sometimes, especially when fatigue sets in, and whether anything more lies beneath can wait. No forced narrative, no unchosen labels—just reality resting at its own pace.",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That is the clearest and most truthful perimeter: you are quieter sometimes, especially",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "fatigue sets in, and whether anything more lies beneath can wait.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "No forced narrative, no unchosen labels—just reality resting at its own pace.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": []
        }
      }
    ]
  },
  {
    "id": "chat-boundaries",
    "topic_id": "boundaries_and_personal_agency",
    "title": "Boundaries and personal agency",
    "date": "Last week · Oct 15",
    "time": "16:10",
    "preview": "A friend keeps asking me to help with tasks when I'm already busy. I usually say yes, even when the timing is bad...",
    "tags": [
      "Boundaries",
      "Agency",
      "Choice"
    ],
    "messages": [
      {
        "role": "user",
        "time": "16:10",
        "rawText": "A friend keeps asking me to help with tasks when I'm already busy. I usually say yes, even when the timing is bad.",
        "text": "A friend keeps asking me to help with tasks when I'm already busy. I usually say yes, even when the timing is bad.",
        "turnData": {
          "rawText": "A friend keeps asking me to help with tasks when I'm already busy. I usually say yes, even when the timing is bad.",
          "maskedText": "A friend keeps asking me to help with tasks when I'm already busy. I usually say yes, even when the timing is bad.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "A friend keeps asking me to help with tasks",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I'm already busy.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "I usually say yes, even",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "the timing is bad.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            },
            {
              "id": "rel_2",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "A friend keeps asking me to help with tasks when I'm already busy.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I usually say yes, even when the timing is bad.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "16:11",
        "paragraphs": [
          "The agreement leaves your lips before the reality of your own schedule has a chance to speak. Saying yes can become an automatic reflex that absorbs their need while crowding out your own. What is that split second like right before you answer?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "The agreement leaves your lips before the reality of your own schedule has a chance to speak. Saying yes can become an automatic reflex that absorbs their need while crowding out your own. What is that split second like right before you answer?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The agreement leaves your lips before the reality of your own schedule has a chance to speak.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Saying yes can become an automatic reflex that absorbs their need",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "crowding out your own.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "What is that split second like right before you answer?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "while",
              "type": "Temporal / Concession",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": true
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:13",
        "rawText": "I don't want them to think I don't care about them.",
        "text": "I don't want them to think I don't care about them.",
        "turnData": {
          "rawText": "I don't want them to think I don't care about them.",
          "maskedText": "I don't want them to think I don't care about them.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I don't want them to think I don't care about them.",
              "sentence": 0
            }
          ],
          "connectors": [],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I don't want them to think I don't care about them.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "them",
              "sentenceIndex": 0,
              "tokenIndex": 3,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            },
            {
              "pronoun": "them",
              "sentenceIndex": 0,
              "tokenIndex": 10,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "16:14",
        "paragraphs": [
          "The refusal feels as though it carries an unintended message: that withholding your labor equates to withholding your care. You are carrying the weight of protecting how they perceive your devotion. Does their opinion feel fragile, or is the fear mostly yours?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "The refusal feels as though it carries an unintended message: that withholding your labor equates to withholding your care. You are carrying the weight of protecting how they perceive your devotion. Does their opinion feel fragile, or is the fear mostly yours?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The refusal feels as",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "it carries an unintended message: that withholding your labor equates to withholding your care.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "You are carrying the weight of protecting how they perceive your devotion.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "Does their opinion feel fragile, or is the fear mostly yours?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "though",
              "type": "Contrast / Concession",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": true
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:16",
        "rawText": "I also genuinely like helping them. It's not as though every request is unwanted.",
        "text": "I also genuinely like helping them. It's not as though every request is unwanted.",
        "turnData": {
          "rawText": "I also genuinely like helping them. It's not as though every request is unwanted.",
          "maskedText": "I also genuinely like helping them. It's not as though every request is unwanted.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I also genuinely like helping them.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "It's not as",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "every request is unwanted.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "though",
              "type": "Contrast / Concession",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": true
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I also genuinely like helping them.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "It's not as though every request is unwanted.",
              "cf": [
                "contemplative_presence"
              ],
              "cp": "contemplative_presence",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "them",
              "sentenceIndex": 0,
              "tokenIndex": 5,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            },
            {
              "pronoun": "its",
              "sentenceIndex": 1,
              "tokenIndex": 1,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "16:17",
        "paragraphs": [
          "The desire to support them is real and comes from an open hand, which makes drawing a boundary feel complicated. You aren't trying to close the door to helping; you're trying to prevent genuine affection from turning into exhaustion. What does it feel like when helping actually feels good?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "The desire to support them is real and comes from an open hand, which makes drawing a boundary feel complicated. You aren't trying to close the door to helping; you're trying to prevent genuine affection from turning into exhaustion. What does it feel like when helping actually feels good?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The desire to support them is real and comes from an open hand, which makes drawing a boundary feel complicated.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "You aren't trying to close the door to helping; you're trying to prevent genuine affection from turning into exhaustion.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What does it feel like",
              "sentence": 2
            },
            {
              "id": "Clause D",
              "text": "helping actually feels good?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:19",
        "rawText": "Yesterday I agreed to something and then felt annoyed with myself because I'd planned to rest.",
        "text": "Yesterday I agreed to something and then felt annoyed with myself because I'd planned to rest.",
        "turnData": {
          "rawText": "Yesterday I agreed to something and then felt annoyed with myself because I'd planned to rest.",
          "maskedText": "Yesterday I agreed to something and then felt annoyed with myself because I'd planned to rest.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Yesterday I agreed to something and then felt annoyed with myself",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I'd planned to rest.",
              "sentence": 0
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Yesterday I agreed to something and then felt annoyed with myself because I'd planned to rest.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "16:20",
        "paragraphs": [
          "The promised rest was given away, and the frustration turned inward against your own compliance. When quiet hours are sacrificed to accommodate someone else, the body remembers the lost clearing. Where in your body did that annoyance settle?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "The promised rest was given away, and the frustration turned inward against your own compliance. When quiet hours are sacrificed to accommodate someone else, the body remembers the lost clearing. Where in your body did that annoyance settle?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The promised rest was given away, and the frustration turned inward against your own compliance.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "When quiet hours are sacrificed to accommodate someone else, the body remembers the lost clearing.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "Where in your body did that annoyance settle?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:22",
        "rawText": "Actually, I wasn't annoyed with my friend. I was frustrated that I hadn't been honest about having other plans.",
        "text": "Actually, I wasn't annoyed with my friend. I was frustrated that I hadn't been honest about having other plans.",
        "turnData": {
          "rawText": "Actually, I wasn't annoyed with my friend. I was frustrated that I hadn't been honest about having other plans.",
          "maskedText": "Actually, I wasn't annoyed with my friend. I was frustrated that I hadn't been honest about having other plans.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Actually, I wasn't annoyed with my friend.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I was frustrated that I hadn't been honest about having other plans.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Actually, I wasn't annoyed with my friend.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I was frustrated that I hadn't been honest about having other plans.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "16:23",
        "paragraphs": [
          "That is a piercing and compassionate clarification. The irritation wasn't about their asking, but about your silence regarding your own needs. Speaking your truth was what was withheld. What made it feel so hard to simply say you had other plans?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "That is a piercing and compassionate clarification. The irritation wasn't about their asking, but about your silence regarding your own needs. Speaking your truth was what was withheld. What made it feel so hard to simply say you had other plans?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That is a piercing and compassionate clarification.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "The irritation wasn't about their asking,",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "about your silence regarding your own needs.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "Speaking your truth was what was withheld.",
              "sentence": 2
            },
            {
              "id": "Clause E",
              "text": "What made it feel",
              "sentence": 3
            },
            {
              "id": "Clause F",
              "text": "hard to simply say you had other plans?",
              "sentence": 3
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "but",
              "type": "Pivot / Counter-condition",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            },
            {
              "id": "rel_2",
              "cue": "so",
              "type": "Result / Consequence",
              "source": "Clause E",
              "target": "Clause F",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:25",
        "rawText": "I told them I couldn't help with the next request because I had already made plans. They said that was completely fine.",
        "text": "I told them I couldn't help with the next request because I had already made plans. They said that was completely fine.",
        "turnData": {
          "rawText": "I told them I couldn't help with the next request because I had already made plans. They said that was completely fine.",
          "maskedText": "I told them I couldn't help with the next request because I had already made plans. They said that was completely fine.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I told them I couldn't help with the next request",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I had already made plans.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "They said that was completely fine.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I told them I couldn't help with the next request because I had already made plans.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "They said that was completely fine.",
              "cf": [
                "contemplative_presence"
              ],
              "cp": "contemplative_presence",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "them",
              "sentenceIndex": 0,
              "tokenIndex": 2,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            },
            {
              "pronoun": "they",
              "sentenceIndex": 1,
              "tokenIndex": 1,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "16:26",
        "paragraphs": [
          "The sky did not fall, and the bond remained unbroken. What felt in anticipation like a dangerous rupture turned out to be ordinary, gracious human understanding. How did the space around you feel the moment they said it was fine?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "The sky did not fall, and the bond remained unbroken. What felt in anticipation like a dangerous rupture turned out to be ordinary, gracious human understanding. How did the space around you feel the moment they said it was fine?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "The sky did not fall, and the bond remained unbroken.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "What felt in anticipation like a dangerous rupture turned out to be ordinary, gracious human understanding.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "How did the space around you feel the moment they said it was fine?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:28",
        "rawText": "I felt relieved afterward, but also a little guilty. Both reactions surprised me.",
        "text": "I felt relieved afterward, but also a little guilty. Both reactions surprised me.",
        "turnData": {
          "rawText": "I felt relieved afterward, but also a little guilty. Both reactions surprised me.",
          "maskedText": "I felt relieved afterward, but also a little guilty. Both reactions surprised me.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I felt relieved afterward,",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "also a little guilty.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "Both reactions surprised me.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "but",
              "type": "Pivot / Counter-condition",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I felt relieved afterward, but also a little guilty.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "Both reactions surprised me.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "16:29",
        "paragraphs": [
          "Relief arrived because your boundary held; guilt arrived because a long-standing habit was disrupted. Those two feelings often walk side by side when you first reclaim territory that belongs to you. Can you let both feelings share the room without apologizing for the relief?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "Relief arrived because your boundary held; guilt arrived because a long-standing habit was disrupted. Those two feelings often walk side by side when you first reclaim territory that belongs to you. Can you let both feelings share the room without apologizing for the relief?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "Relief arrived",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "your boundary held; guilt arrived because a long-standing habit was disrupted.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "Those two feelings often walk side by side",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "you first reclaim territory that belongs to you.",
              "sentence": 1
            },
            {
              "id": "Clause E",
              "text": "Can you let both feelings share the room without apologizing for the relief?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            },
            {
              "id": "rel_2",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause C",
              "target": "Clause D",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:31",
        "rawText": "I still want to help when I can. I just don't want to automatically treat every request as something I have to agree to.",
        "text": "I still want to help when I can. I just don't want to automatically treat every request as something I have to agree to.",
        "turnData": {
          "rawText": "I still want to help when I can. I just don't want to automatically treat every request as something I have to agree to.",
          "maskedText": "I still want to help when I can. I just don't want to automatically treat every request as something I have to agree to.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I still want to help",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I can.",
              "sentence": 0
            },
            {
              "id": "Clause C",
              "text": "I just don't want to automatically treat every request as something I have to agree to.",
              "sentence": 1
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I still want to help when I can.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I just don't want to automatically treat every request as something I have to agree to.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "16:32",
        "paragraphs": [
          "You are separating voluntary generosity from compulsory compliance. Generosity has life only when refusal is genuinely permitted; otherwise, it is simply duty wearing a smile. How does helping feel when you know you could just as easily say no?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "You are separating voluntary generosity from compulsory compliance. Generosity has life only when refusal is genuinely permitted; otherwise, it is simply duty wearing a smile. How does helping feel when you know you could just as easily say no?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "You are separating voluntary generosity from compulsory compliance.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Generosity has life only",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "refusal is genuinely permitted; otherwise, it is simply duty wearing a smile.",
              "sentence": 1
            },
            {
              "id": "Clause D",
              "text": "How does helping feel",
              "sentence": 2
            },
            {
              "id": "Clause E",
              "text": "you know you could just as easily say no?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause B",
              "target": "Clause C",
              "symmetric": false
            },
            {
              "id": "rel_2",
              "cue": "when",
              "type": "Temporal / Anchor",
              "source": "Clause D",
              "target": "Clause E",
              "symmetric": false
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:34",
        "rawText": "Today I said yes to a different request because I actually had time and wanted to do it.",
        "text": "Today I said yes to a different request because I actually had time and wanted to do it.",
        "turnData": {
          "rawText": "Today I said yes to a different request because I actually had time and wanted to do it.",
          "maskedText": "Today I said yes to a different request because I actually had time and wanted to do it.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "Today I said yes to a different request",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I actually had time and wanted to do it.",
              "sentence": 0
            }
          ],
          "connectors": [
            {
              "id": "rel_1",
              "cue": "because",
              "type": "Causal / Explanation",
              "source": "Clause A",
              "target": "Clause B",
              "symmetric": false
            }
          ],
          "recurringTopics": [],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "Today I said yes to a different request because I actually had time and wanted to do it.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            }
          ],
          "hobbsData": [
            {
              "pronoun": "it",
              "sentenceIndex": 0,
              "tokenIndex": 17,
              "resolvedAntecedent": "[unspoken obligation]",
              "candidates": [
                {
                  "entity": "[unspoken obligation]",
                  "sentenceDistance": 1,
                  "agreement": true,
                  "rank": 1,
                  "role": "prior_nominal"
                }
              ],
              "status": "resolved"
            }
          ]
        }
      },
      {
        "role": "assistant",
        "time": "16:35",
        "paragraphs": [
          "That 'yes' had ground beneath it. Because you had room and an authentic desire, giving your time restored rather than diminished you. What was the quality of that yes compared to the ones given under pressure?"
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "That 'yes' had ground beneath it. Because you had room and an authentic desire, giving your time restored rather than diminished you. What was the quality of that yes compared to the ones given under pressure?",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That 'yes' had ground beneath it.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Because you had room and an authentic desire, giving your time restored rather than diminished you.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "What was the quality of that yes compared to the ones given under pressure?",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            },
            {
              "term": "contemplative_presence",
              "label": "CONTINUE",
              "detail": "Centering CONTINUE (cost: 0)",
              "status": "Linked"
            }
          ]
        }
      },
      {
        "role": "user",
        "time": "16:37",
        "rawText": "I think the difference is whether I choose to help or feel like I have no real choice. I'm still figuring out how to recognize that in the moment.",
        "text": "I think the difference is whether I choose to help or feel like I have no real choice. I'm still figuring out how to recognize that in the moment.",
        "turnData": {
          "rawText": "I think the difference is whether I choose to help or feel like I have no real choice. I'm still figuring out how to recognize that in the moment.",
          "maskedText": "I think the difference is whether I choose to help or feel like I have no real choice. I'm still figuring out how to recognize that in the moment.",
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "entitiesMasked": 0,
          "clauses": [
            {
              "id": "Clause A",
              "text": "I think the difference is whether I choose to help or feel like I have no real choice.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "I'm still figuring out how to recognize that in the moment.",
              "sentence": 1
            }
          ],
          "connectors": [],
          "recurringTopics": [
            {
              "term": "speaker:self",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ],
          "centeringTrace": [
            {
              "sentence": 0,
              "sentenceText": "I think the difference is whether I choose to help or feel like I have no real choice.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": null,
              "transition": "NO_CB",
              "cost": 3
            },
            {
              "sentence": 1,
              "sentenceText": "I'm still figuring out how to recognize that in the moment.",
              "cf": [
                "speaker:self"
              ],
              "cp": "speaker:self",
              "cb": "speaker:self",
              "transition": "INITIAL_CB",
              "cost": 1
            }
          ],
          "hobbsData": []
        }
      },
      {
        "role": "assistant",
        "time": "16:38",
        "paragraphs": [
          "That distinction is the core of personal agency: voluntary gift versus unchosen obligation. Learning to pause long enough in the moment to feel which one is speaking takes practice and patience. You don't have to master it overnight—noticing it right now is already the change."
        ],
        "turnData": {
          "entity": "[Boundaries]",
          "entityType": "Local RAM Session",
          "maskedText": "That distinction is the core of personal agency: voluntary gift versus unchosen obligation. Learning to pause long enough in the moment to feel which one is speaking takes practice and patience. You don't have to master it overnight—noticing it right now is already the change.",
          "clauses": [
            {
              "id": "Clause A",
              "text": "That distinction is the core of personal agency: voluntary gift versus unchosen obligation.",
              "sentence": 0
            },
            {
              "id": "Clause B",
              "text": "Learning to pause long enough in the moment to feel which one is speaking takes practice and patience.",
              "sentence": 1
            },
            {
              "id": "Clause C",
              "text": "You don't have to master it overnight—noticing it right now is already the change.",
              "sentence": 2
            }
          ],
          "connectors": [
            {
              "cue": "while",
              "text": "while",
              "type": "Syntactic Balance"
            }
          ],
          "recurringTopics": [
            {
              "term": "contemplative_presence",
              "label": "INITIAL_CB",
              "detail": "Centering INITIAL_CB (cost: 1)",
              "status": "Linked"
            }
          ]
        }
      }
    ]
  }
];

export const HISTORICAL_MEMORIES = [
  {
    "id": "mem-achievement",
    "title": "Giving room to enjoy the achievement",
    "date": "Oct 24, 2026",
    "quote": "I'm proud of what I achieved, physically tired from getting here, and trying to give myself room to enjoy it before moving on.",
    "centerEntity": "achievement",
    "context": "Discovered that fatigue was physical exhaustion from preparation, not an unfulfilled need to prove worth.",
    "stoneCount": 4,
    "transition": "CONTINUE",
    "tags": [
      "Achievement",
      "Pacing",
      "Rest"
    ]
  },
  {
    "id": "mem-pattern",
    "title": "Useful planning versus delayed action",
    "date": "Oct 22, 2026",
    "quote": "Planning helps when the task is genuinely complicated. It becomes a problem when I keep planning after I already know enough to begin.",
    "centerEntity": "planning",
    "context": "Distinguished genuine problem organization from continued preparation motivated by fear of judgment.",
    "stoneCount": 3,
    "transition": "SMOOTH_SHIFT",
    "tags": [
      "Planning",
      "Observation",
      "Action"
    ]
  },
  {
    "id": "mem-resistance",
    "title": "Allowing the story to stay unresolved",
    "date": "Oct 19, 2026",
    "quote": "I don't want to force an explanation just so the story makes sense. I'm okay with not knowing yet.",
    "centerEntity": "uncertainty",
    "context": "Rejected the artificial fear framing. Honored low energy and tiredness without forcing narrative closure.",
    "stoneCount": 4,
    "transition": "CONTINUE",
    "tags": [
      "Stillness",
      "Autonomy",
      "Uncertainty"
    ]
  },
  {
    "id": "mem-boundaries",
    "title": "Voluntary help versus unchosen obligation",
    "date": "Oct 15, 2026",
    "quote": "I think the difference is whether I choose to help or feel like I have no real choice. I'm still figuring out how to recognize that in the moment.",
    "centerEntity": "choice",
    "context": "Separated authentic desire to support a friend from automatic self-sacrificing compliance.",
    "stoneCount": 3,
    "transition": "SMOOTH_SHIFT",
    "tags": [
      "Boundaries",
      "Agency",
      "Choice"
    ]
  }
];
