"""Embedded quest snapshot, generated from the game files.

Source: tools/icon_extractor --quests mode (CUE4Parse static pak read,
Agility update). Regenerate: dotnet run -c Release -- --quests in
tools/icon_extractor, then rebuild this file from quests_dump.json.

quest_id matches GameProgress.QuestProgress.Quests[].QuestId in saves.
Reward types: item (inventory item + count), recipe_unlock (id is
strict-mode-safe, present in EMBEDDED_RECIPE_IDS), mount_unlock (asset
name; prefix MountDataAsset: when writing to MountsUnlockedList).
"""

EMBEDDED_QUESTS = [{'quest_id': '3MpWS0mD8A6yFVmjVAA2Qg',
  'asset': 'Quest_DR_MainQuest',
  'name': "Black Knight's Fortress",
  'description': 'Uncover the secrets of Dowdun Reach in order to unlock your '
                 'way through to the Umbral Sands.',
  'category': 'main',
  'region': None,
  'rewards': [{'item_id': 'PzF6r0v9aps3QVSoWKGy0A',
               'asset': 'RECIPE_Masterworks_Weapon_GreatSword_TitansWrath',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'mQeJ6kJZdcr49cGHQ1qcHw',
               'asset': 'ITEM_Consumable_BlackKnightFortresssRewardPack1',
               'count': 1,
               'type': 'item'}],
  'objectives': ['DR_Main_Objective_0',
                 'DR_Main_Objective_1',
                 'DR_Main_Objective_2',
                 'DR_Main_Objective_3',
                 'DR_Main_Objective_4',
                 'DR_Main_Objective_5',
                 'DR_Main_Objective_6',
                 'DR_Main_Objective_-1',
                 'DR_Main_Objective_4_1',
                 'DR_Main_Objective_4_2',
                 'DR_Main_Objective_4_3',
                 'DR_Main_Objective_4_4',
                 'DR_Main_Objective_4_5',
                 'DR_Main_Objective_4_6',
                 'DR_Main_Objective_4_7',
                 'DR_Main_Objective_4_8',
                 'DR_Main_Objective_4_9',
                 'DR_Main_Objective_4_10',
                 'DR_Main_Objective_4_11',
                 'DR_Main_Objective_4_12',
                 'DR_Main_Objective_4_13',
                 'DR_Main_Objective_4_-1'],
  'objective_texts': {'DR_Main_Objective_0': 'Speak to Cathan at the eastern '
                                             'gates in Fellhollow',
                      'DR_Main_Objective_1': 'Speak to the Wise Old Man In '
                                             'Dowdun Reach',
                      'DR_Main_Objective_2': 'Speak to Doric in Dowdun Reach',
                      'DR_Main_Objective_3': 'Investigate the Dreaming Stone',
                      'DR_Main_Objective_4': 'Collect the Shards of the '
                                             'Dreaming Stone around Dowdun '
                                             'Reach: 0/13',
                      'DR_Main_Objective_5': 'Defeat the Gatekeeper',
                      'DR_Main_Objective_6': 'Return to the Dreaming Stone',
                      'DR_Main_Objective_-1': 'Speak To Death',
                      'DR_Main_Objective_4_1': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 1/13',
                      'DR_Main_Objective_4_2': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 2/13',
                      'DR_Main_Objective_4_3': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 3/13',
                      'DR_Main_Objective_4_4': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 4/13',
                      'DR_Main_Objective_4_5': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 5/13',
                      'DR_Main_Objective_4_6': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 6/13',
                      'DR_Main_Objective_4_7': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 7/13',
                      'DR_Main_Objective_4_8': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 8/13',
                      'DR_Main_Objective_4_9': 'Collect the Shards of the '
                                               'Dreaming Stone around Dowdun '
                                               'Reach: 9/13',
                      'DR_Main_Objective_4_10': 'Collect the Shards of the '
                                                'Dreaming Stone around Dowdun '
                                                'Reach: 10/13',
                      'DR_Main_Objective_4_11': 'Collect the Shards of the '
                                                'Dreaming Stone around Dowdun '
                                                'Reach: 11/13',
                      'DR_Main_Objective_4_12': 'Collect the Shards of the '
                                                'Dreaming Stone around Dowdun '
                                                'Reach: 12/13',
                      'DR_Main_Objective_4_13': 'Return to the Dreaming Stone',
                      'DR_Main_Objective_4_-1': 'Speak to Doric about the '
                                                'shards around Dowdun Reach'}},
 {'quest_id': 'yrRZnkmro-IvH_OmZ3f-5A',
  'asset': 'Quest_DragonSlayer',
  'name': 'Dragon Slayer',
  'description': 'Recruited with promises of glory, your first challenge is to '
                 'defeat General Velgar.',
  'category': 'main',
  'region': None,
  'rewards': [{'item_id': '5MXdoES87BjPNAa2O22Qcg',
               'asset': 'RECIPE_Masterworks_Shield_Dragonfire',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'zGz3MkD3vLq_D1uuA2S44g',
               'asset': 'ITEM_Consumable_DragonSlayerRewardPackBeat5',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Claim a bed',
                 'Return to the Wise old man after claimed bed',
                 'Find and hunt a deer',
                 'Investigate the castle',
                 'Locate cathan in the vault',
                 'Return to the Wise old man',
                 'Venture into Ghornfell',
                 'Look for evidence of Cathan at the tower',
                 'Craft the summon horn',
                 'Challenge Velgar',
                 'Return to the Wise old man after killing velgar'],
  'objective_texts': {'Claim a bed': 'Construct a base of operations in '
                                     'Bramblemead village. Build a shelter and '
                                     'claim a bed.',
                      'Return to the Wise old man after claimed bed': 'Speak '
                                                                      'to the '
                                                                      'Wise '
                                                                      'Old Man '
                                                                      'in '
                                                                      'Bramblemead '
                                                                      'village.',
                      'Find and hunt a deer': 'Hunt a deer and bring one of '
                                              'its antlers to the Wise Old '
                                              'Man.',
                      'Investigate the castle': 'Siege the goblin castle and '
                                                'look for Cathan.',
                      'Locate cathan in the vault': 'Investigate the '
                                                    'blue-flame door in the '
                                                    'swamp. Find out what '
                                                    'Cathan is up to.',
                      'Return to the Wise old man': 'Speak to the Wise Old Man '
                                                    'in Bramblemead village.',
                      'Venture into Ghornfell': 'Gear yourself up and push '
                                                'forward into Ghornfell in '
                                                'search of Cathan.',
                      'Look for evidence of Cathan at the tower': 'Investigate '
                                                                  "Velgar's "
                                                                  'tower in '
                                                                  'search of '
                                                                  'Cathan.',
                      'Craft the summon horn': 'Find the ingredients and craft '
                                               'the Challenge Horn. Check the '
                                               'recipe in your journal for '
                                               'more information.',
                      'Challenge Velgar': 'Summon and defeat Velgar.',
                      'Return to the Wise old man after killing velgar': 'Bring '
                                                                         "Velgar's "
                                                                         'head '
                                                                         'to '
                                                                         'the '
                                                                         'Wise '
                                                                         'Old '
                                                                         'Man '
                                                                         'outside '
                                                                         "Velgar's "
                                                                         'Lair.'}},
 {'quest_id': 'kPtTW0exXrqw2BqELR_bFA',
  'asset': 'Quest_UmS_MainQuest',
  'name': "Icthlarin's Little Helper",
  'description': 'Slay the tyrant dragon Fuzan and unite the Moon Garou along '
                 'the way',
  'category': 'main',
  'region': None,
  'rewards': [{'item_id': 'myqnDkdJSshMLUq3sMlSLA',
               'asset': 'RECIPE_Weapon_Shield_FuzanDragonfireShield',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': '-ScWrUBProaGeVmYdfrJAg',
               'asset': 'ITEM_Consumable_Ums_MQ_RewardPack_Complete',
               'count': 1,
               'type': 'item'}],
  'objectives': ['FindGarou',
                 'InvestigateGarouProblem',
                 'ReturnToFirstGarou',
                 'FindThreeKeys',
                 'FightFuzan',
                 'ReturnToIcthlarin',
                 'FirstGarouEarnReputation.NoReputation',
                 'FirstGarouEarnReputation.LowReputation',
                 'FirstGarouEarnReputation.MediumReputation',
                 'FirstGarouEarnReputation.HighReputation',
                 'FirstGarouEarnReputation.MaxReputation',
                 'SpeakToIcthlarin',
                 'SpeakToGarouElder',
                 'RepairTheMirrors',
                 'SlayFuzan',
                 'LookForLife',
                 'EnterUmS',
                 'FindLastKey'],
  'objective_texts': {'FindGarou': 'Speak to the Alcarrid Elder in the Moon '
                                   'Garou settlement to the south',
                      'InvestigateGarouProblem': 'Investigate the nearby area '
                                                 'for something that concerns '
                                                 'the Moon Garou',
                      'ReturnToFirstGarou': 'Return to Shangruuh, the Alcarrid '
                                            'Envoy in the passage from Dowdun '
                                            'Reach',
                      'FindThreeKeys': 'Travel to Moon Garou camps, find their '
                                       'elders, and earn their trust to gain '
                                       'their Mirror Lenses',
                      'FightFuzan': 'Enter the Fight Caves and defeat Fuzan',
                      'ReturnToIcthlarin': "Bring Fuzan's head to Icthlarin at "
                                           'the Mirror Relay',
                      'FirstGarouEarnReputation.NoReputation': 'Gain the trust '
                                                               'of the '
                                                               'Alcarrid Camp',
                      'FirstGarouEarnReputation.LowReputation': 'Gain the '
                                                                'trust of the '
                                                                'Alcarrid Camp',
                      'FirstGarouEarnReputation.MediumReputation': 'Gain the '
                                                                   'trust of '
                                                                   'the '
                                                                   'Alcarrid '
                                                                   'Camp',
                      'FirstGarouEarnReputation.HighReputation': 'Gain the '
                                                                 'trust of the '
                                                                 'Alcarrid '
                                                                 'Camp',
                      'FirstGarouEarnReputation.MaxReputation': 'You have '
                                                                'completed the '
                                                                "tribe's "
                                                                'tasks. Return '
                                                                'to the '
                                                                'Alcarrid '
                                                                'Elder',
                      'SpeakToIcthlarin': 'Speak to Icthlarin at the Mirror '
                                          'Relay',
                      'SpeakToGarouElder': 'Speak to the Alcarrid Elder and '
                                           'complete tasks to earn their trust',
                      'RepairTheMirrors': 'Place the three Mirror Lenses into '
                                          'the Mirror Relay',
                      'SlayFuzan': 'Journey through the Fight Caves and slay '
                                   'Fuzan',
                      'LookForLife': 'Look for signs of life in the desert',
                      'EnterUmS': 'Enter the Umbral Sands',
                      'FindLastKey': 'Complete tasks for the final camp and '
                                     'gain their Mirror Lens'}},
 {'quest_id': 'uftGB0es-CGrvXyPoxW31w',
  'asset': 'Quest_DeathQuestMain',
  'name': 'Withering Heights',
  'description': 'Put an end to the horror of Fellhollow, by defeating Imaru, '
                 'the soul-devourer.',
  'category': 'main',
  'region': None,
  'rewards': [{'item_id': 'V6JWS0Q-GuvrJS2f3-c_DA',
               'asset': 'RECIPE_Masterworks_Shield_Dragonfire_Imaru',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'rCw_tULBJw2cbgiNTYjmuQ',
               'asset': 'ITEM_Consumable_DeathquestRewardPack',
               'count': 1,
               'type': 'item'}],
  'objectives': ['TalkToWomNEGF',
                 'UnlockGate',
                 'SearchTheStructure',
                 'SpeakToMysteriousFigure',
                 'SpeakToPostiePete',
                 'GoThroughDoorToFH',
                 'FindACleansingPool',
                 'InvestigateStandingStones',
                 'ReachedStandingStones',
                 'InteractedWithStone1',
                 'InteractedWithStone2',
                 'BreakTheThreeSeals',
                 'BreakRemainingtwoSeals',
                 'BreakTheFinalSeal',
                 'ChallangeImaru',
                 'ReturnToDeath'],
  'objective_texts': {'TalkToWomNEGF': 'Speak to the Wise Old Man near '
                                       "Ashien's Watch.",
                      'UnlockGate': 'Unlock the strange door.',
                      'SearchTheStructure': "Speak to the temple's inhabitant.",
                      'SpeakToMysteriousFigure': 'Speak to Death.',
                      'SpeakToPostiePete': 'Speak to Postie Pete.',
                      'GoThroughDoorToFH': 'Enter Fellhollow.',
                      'FindACleansingPool': 'Remove the Soul Rift at a '
                                            'Purification Pool.',
                      'InvestigateStandingStones': 'Find Cathan and look into '
                                                   'what he was investigating.',
                      'ReachedStandingStones': 'Get location of curse '
                                               'fragments 0/3.',
                      'InteractedWithStone1': 'Get location of curse fragments '
                                              '1/3.',
                      'InteractedWithStone2': 'Get location of curse fragments '
                                              '2/3.',
                      'BreakTheThreeSeals': 'Gather three curse fragments from '
                                            'the locations described in the '
                                            'standing stones.',
                      'BreakRemainingtwoSeals': 'Gather two more curse '
                                                'fragments from the locations '
                                                'described in the standing '
                                                'stones.',
                      'BreakTheFinalSeal': 'Find the last curse fragment from '
                                           'the locations described in the '
                                           'standing stones.',
                      'ChallangeImaru': 'Enter the Shattered Spire and defeat '
                                        'Imaru.',
                      'ReturnToDeath': "Bring Imaru's head to Death."}},
 {'quest_id': '2V1KS0R3XJX-UtiuP78EoA',
  'asset': 'Quest_SaradominStatue',
  'name': '[PH] Saradomin Statue',
  'description': '[PH]',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'vzW7t03sYSXuT4WJK8s6YQ',
               'asset': 'RECIPE_Armour_T0_Cape_Saradominist',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'wEW2qEiffVgFFlmRJse7yg',
               'asset': 'ITEM_Cape_Saradominist',
               'count': 1,
               'type': 'item'}],
  'objectives': [],
  'objective_texts': {}},
 {'quest_id': 'UPSTQ0y_YVdTjyO6nWKZiQ',
  'asset': 'Quest_UmS_Vannaka',
  'name': '[PH] Vannaka UmS',
  'description': '[PH] Vannaka is fascinated by the Kalphite. Help him '
                 'understand them more.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'nFRdHU7L4A3xRjOWjzMzoQ',
               'asset': 'RECIPE_Armour_T0_Cape_Chinchompa',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'uqGAn0tZnBkZEJSwmx70KA',
               'asset': 'ITEM_Cape_Chinchompa',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': '[PH] Bring a Kalphite shell to Vannaka to '
                                    'study',
                      'Objective2': '[PH] Bring a Kalphite wing back to '
                                    'Vannaka for him to study',
                      'Objective3': '[PH] Bring some Kalphite ichor back to '
                                    'Vannaka'}},
 {'quest_id': 'O3ruOkgGHBqwIheSH_7BBg',
  'asset': 'Quest_AMelodyRemebered',
  'name': 'A Melody Remembered',
  'description': 'A jewellery box in Ghornfell plays a haunting melody, but it '
                 'cannot complete its song.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'UufnwENDSDFYKSG9v8yO8g',
               'asset': 'RECIPE_Trinket_Ring_Ravanna',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'mqzn-kOXtYJX-Qedojuu3Q',
               'asset': 'ITEM_Trinket_Ravannas_Ring',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1', 'Objective2'],
  'objective_texts': {'Objective1': 'The jewellery box requires a specific '
                                    'ring.',
                      'Objective2': 'The jewellery box requires a specific '
                                    'amulet.'}},
 {'quest_id': '4G_ph0XQeA1Nc72_CVO6HQ',
  'asset': 'Quest_ElderGarou',
  'name': 'A Room with a Garou',
  'description': 'An elder garou wants you to build a home that his late wife '
                 'would be proud of.',
  'category': 'side',
  'region': None,
  'rewards': [],
  'objectives': ['None'],
  'objective_texts': {'None': 'Build a home around Caratacus the Elder.'}},
 {'quest_id': '0WS3LUBsaPUDeuiPT_akhQ',
  'asset': 'Quest_AnimalMagnetism',
  'name': 'Animal Magnetism',
  'description': "Create the Ava's Accumulator",
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'PndrsEclFELVGiGeuw6HDQ',
               'asset': 'RECIPE_Armour_T0_Cape_Avas_Accumulator',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'AA0zK0IPgo4C4e6V39Cmjg',
               'asset': 'ITEM_Cape_Avas_Accumulator',
               'count': 1,
               'type': 'item'}],
  'objectives': ['None', 'Objective2', 'Objective3', 'Objective4'],
  'objective_texts': {'None': 'Read the Advert-Inna-Bottle next to Manktongue',
                      'Objective2': 'Discuss the advert with Manktongue',
                      'Objective3': 'Gather an undead chicken, magnetised iron '
                                    'bar and undead twigs, and bring them to '
                                    'Manktongue',
                      'Objective4': 'Return to Manktongue'}},
 {'quest_id': '0cB0D0QD_L4nrpu6CxZEsw',
  'asset': 'Quest_UmS_MainQuest1_TribeC_Task1',
  'name': 'Beast in the Sand',
  'description': 'Follow the trail of the Dearg Due to the south, and retrieve '
                 'the body of its victim. ',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'WqpIPU7dFtswfcaDoldlYg',
               'asset': 'ITEM_Resources_Currency_Chit_Garou',
               'count': 200,
               'type': 'item'}],
  'objectives': ['FollowBeast', 'GiveWater', 'Return'],
  'objective_texts': {'FollowBeast': 'Track down the Dearg Due through the '
                                     'sandstorm',
                      'GiveWater': 'Give Efina - The Lost some clean water',
                      'Return': 'Return to Manathep - The Bereaved'}},
 {'quest_id': '2kXJ3kWFS38kZfmPnvUFXw',
  'asset': 'Quest_SQ3_Nevermore',
  'name': 'Biohazard',
  'description': 'Investigate the strange corruption afflicting the residents '
                 'of Dowdun Reach.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': '8L37OE7i2JOHvnKTu-_-xw',
               'asset': 'ITEM_Cape_Zamorak',
               'count': 1,
               'type': 'item'},
              {'item_id': 'izVmUEXJXkUCLfea_tl2WQ',
               'asset': 'RECIPE_Armour_T0_Cape_Zamorak',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['DR_SQ3_EntryPickup',
                 'DR_SQ3_HuntRavens',
                 'DR_SQ3_FindIngredients',
                 'DR_SQ3_LocateSource',
                 'DR_SQ3_FinalBeat'],
  'objective_texts': {'DR_SQ3_EntryPickup': 'Speak to Zanik about the '
                                            'Corrupted Essence you got from a '
                                            'strange raven.',
                      'DR_SQ3_HuntRavens': 'Gather 10 biological samples from '
                                           'strange ravens in Dowdun Reach, '
                                           'and bring them to Zanik.',
                      'DR_SQ3_FindIngredients': 'Bring Zanik the ingredients. '
                                                'Dragons Blood. A Twilight '
                                                'Lily and some Unholy Water.',
                      'DR_SQ3_LocateSource': 'Find the source of the cthonian '
                                             'infection, somewhere high up in '
                                             'Dowdun Reach.',
                      'DR_SQ3_FinalBeat': 'Return to Zanik and explain the '
                                          'situation.'}},
 {'quest_id': 'sQ91eUA55bcQx0OQ0m59sg',
  'asset': 'Quest_BrinkOfExtinction',
  'name': 'Brink of Extinction',
  'description': 'Help Zi to become a real KotHaar',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'vOcsbU0QCoj9Z3C-XFDLAA',
               'asset': 'DA_Consumable_Vestige_Armour_Cape_Obsidian',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective5',
                 'Objective1',
                 'Objective2',
                 'Objective2.1',
                 'Objective2.2',
                 'Objective3',
                 'Objective2.3',
                 'Objective4',
                 'Objective6'],
  'objective_texts': {'Objective5': 'Use the KotHaar numbering book to get '
                                    'past the KotHaar Bouncer',
                      'Objective1': 'Bring 1 cactus steak and 3 raw beltfish '
                                    'back to Zi in Umbral Sands',
                      'Objective2': 'Touch 4 pedestals in any order in THE '
                                    'GAUNTLET OF FIRE - 0/4',
                      'Objective2.1': 'Touch 4 pedestals in any order in THE '
                                      'GAUNTLET OF FIRE - 1/4',
                      'Objective2.2': 'Touch 4 pedestals in any order in THE '
                                      'GAUNTLET OF FIRE - 2/4',
                      'Objective3': 'Return to Zi in the Burning Spire region '
                                    'of the Umbral Sands',
                      'Objective2.3': 'Touch 4 pedestals in any order in THE '
                                      'GAUNTLET OF FIRE - 3/4',
                      'Objective4': 'Use the password to enter the Cave of '
                                    'Screams, within the Burning Spire region',
                      'Objective6': 'Return to the KotHaar Bouncer outside of '
                                    'the Cave of Screams'}},
 {'quest_id': 'A3DOkkGZxXUHc82rPKHznA',
  'asset': 'Quest_Contact',
  'name': 'Contact!',
  'description': "Work with Avisk to find a potential shortcut to Fuzan's "
                 'Volcano',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'nPHTJky85bBWiI-YMJIatA',
               'asset': 'RECIPE_Weapon_Staff_PharaohSceptre',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['Objective1',
                 'Objective2',
                 'Objective4',
                 'Objective5',
                 'Objective2.1',
                 'Objective6',
                 'Objective3',
                 'Objective7',
                 'CrystalShard.1',
                 'CrystalShard.2'],
  'objective_texts': {'Objective1': 'Find the Vault Guardian Prime in the '
                                    'Kalphite Hive',
                      'Objective2': 'Find 3 missing vault guardians and '
                                    'recover their Crystal Helix fragments',
                      'Objective4': 'Use the Crystal Helix to pass through the '
                                    'magical barrier in the Kalphite Hive',
                      'Objective5': 'Talk to Zanik in the Shortcut Chamber '
                                    'within the Kalphite Hive',
                      'Objective2.1': 'Follow the footsteps in the sand to '
                                      'find who made them',
                      'Objective6': 'Break the four crystals in the Shortcut '
                                    'Chamber of the Kalphite Hive',
                      'Objective3': 'Return to the Vault Guardian Prime',
                      'Objective7': 'Return to Zanik in the Shortcut Chamber '
                                    'within the Kalphite Hive',
                      'CrystalShard.1': 'Find Crystal Helix fragments. 1/3',
                      'CrystalShard.2': 'Find Crystal Helix fragments. 2/3'}},
 {'quest_id': 'cZlfrUaPSsi4VfeVc6iIEw',
  'asset': 'Quest_CooksAssistant',
  'name': "Cook's Assistant",
  'description': 'Help Slopfinger in Ghornfell bake a memorable cake for '
                 'Manktongue.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'CK4wDUh8yB5bTq-Ncx2LjA',
               'asset': 'RECIPE_Consumable_Cake_VictoriaSpongeCake',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['Objective1',
                 'Objective2',
                 'Objective3',
                 'Objective4',
                 'Objective5'],
  'objective_texts': {'Objective1': 'Gather 4 eggs, 6 wheat and a bucket of '
                                    'milk, and bring them all to Slopfinger.',
                      'Objective2': 'Bake a cake using the stove next to '
                                    'Slopfinger.',
                      'Objective3': 'Bring the signed cake to Manktongue.',
                      'Objective4': 'Show Slopfinger the freshly cooked cake.',
                      'Objective5': 'Give Slopfinger the good news.'}},
 {'quest_id': 'Kdj6N0dEw05JjoyDP0pNvw',
  'asset': 'Quest_DogDays',
  'name': 'Dog Days',
  'description': 'Investigate the Garou and their rituals.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'q6popEFaVyrZbq6kc0-Drg',
               'asset': 'ITEM_Cape_Garou',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1',
                 'Objective2',
                 'Objective3',
                 'Objective4',
                 'Objective5',
                 'Objective6'],
  'objective_texts': {'Objective1': 'Search Garou camps beneath giant wyrm '
                                    'bones in the Highlands for information on '
                                    'Garou ritual practices.',
                      'Objective2': 'Challenge a Garou king in their Highland '
                                    'stronghold and claim their token.',
                      'Objective3': 'Search garou camps beneath the giant wyrm '
                                    'bones in the Highlands for information on '
                                    "the King's Token.",
                      'Objective4': 'Complete the ritual of purification on '
                                    "the King's Token at the ancient shrine "
                                    'where "a heart once beat".',
                      'Objective5': "Bring the Purified King's Token to "
                                    'Vannaka in the Ghornfell Highlands.',
                      'Objective6': 'Search the Ghornfell Highlands for a '
                                    'friendly face with an interest in Garou '
                                    'rituals.'}},
 {'quest_id': 'Fv3Rt0Dn18PT1DepNzEqtQ',
  'asset': 'Quest_FH_CollectorsCalling',
  'name': "Doric's Quest",
  'description': 'Doric is looking for rare weapons in Fellhollow. ',
  'category': 'side',
  'region': None,
  'rewards': [],
  'objectives': ['FindSkeletonShortbow',
                 'FindShadowSword',
                 'FindNecromancerStaff',
                 'SpeakToDoric'],
  'objective_texts': {'FindSkeletonShortbow': "Craft an Undead Ranger's Bow "
                                              'and bring it to Doric in '
                                              'Fellhollow. Doric believes the '
                                              'recipe is in a vault somewhere.',
                      'FindShadowSword': 'Craft a Shadow Sword and bring it to '
                                         'Doric in Fellhollow. Doric believes '
                                         'a zogre has the recipe.',
                      'FindNecromancerStaff': "Craft a Necromancer's Staff and "
                                              'bring it to Doric in '
                                              'Fellhollow. Doric believes the '
                                              'recipe is in a vault somewhere.',
                      'SpeakToDoric': 'Speak to Doric in Fellhollow.'}},
 {'quest_id': '4QQuNkR6spTCXC6zj6VqxQ',
  'asset': 'Quest_FH_GhostQuest',
  'name': 'Even More Restless Ghosts',
  'description': 'Help Zanik lay some spirits to rest by finding them and '
                 'completing their unfinished business. ',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'gfYV7Ei7CxmoZTSSfBeQfQ',
               'asset': 'RECIPE_Resources_CrossbowLimbs_Dorgeshuun',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': '_teiH085-W3JD5m7UbpBbA',
               'asset': 'RECIPE_Ammo_Bolts_Bone',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'Kh__9UjWDAEtYEuunTYtQA',
               'asset': 'RECIPE_Weapon_Crossbow_Dorgeshuun',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['FindGhosts0/3',
                 'FindGhosts1/3',
                 'FindGhosts2/3',
                 'BackToZanik',
                 'BackToZanikNotSpokenToZanik'],
  'objective_texts': {'FindGhosts0/3': 'Find ghosts and complete their '
                                       'unfinished business. (0/3)',
                      'FindGhosts1/3': 'Find ghosts and complete their '
                                       'unfinished business. (1/3)',
                      'FindGhosts2/3': 'Find ghosts and complete their '
                                       'unfinished business. (2/3)',
                      'BackToZanik': 'Return to Zanik.',
                      'BackToZanikNotSpokenToZanik': 'Tell someone about these '
                                                     'spirits. '}},
 {'quest_id': 'AsyEt0xjewNEzYmzr_kg_w',
  'asset': 'Quest_GoblinDiplomacy',
  'name': 'Goblin Diplomacy',
  'description': "Zanik needs you to stop a prophecy before it's too late.",
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': '24_UV0P2zlDAbcy48UOCkA',
               'asset': 'ITEM_Cape_Goblin',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1',
                 'Objective2a',
                 'Objective2b',
                 'Objective3',
                 'Objective4',
                 'Objective5',
                 'Objective6'],
  'objective_texts': {'Objective1': 'Investigate the ruins to the northeast '
                                    'and the guild to the south of Zanik.',
                      'Objective2a': 'Investigate the ruin northeast of Zanik.',
                      'Objective2b': 'Investigate the guild south of Zanik.',
                      'Objective3': 'Search for the other amulet piece in an '
                                    'area filled with mud and stagnant '
                                    'swampwater.',
                      'Objective4': 'Bring both amulets to Zanik.',
                      'Objective5': 'Look for the other amulet at either the '
                                    'ruins northeast of Zanik, or the guild to '
                                    'the south.',
                      'Objective6': 'Find someone that can identify the '
                                    'Bandosian amulet.'}},
 {'quest_id': 'bsfNlkgT8D_Y5HCdCf-Seg',
  'asset': 'Quest_GraniteMauled',
  'name': 'Granite Mauled',
  'description': "Uncover the secrets of Ashien's Watch.",
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'TRQBZ0gufJDy-HWCsXysNw',
               'asset': 'ITEM_Masterworks_Imbued_Granite_Maul_Head',
               'count': 1,
               'type': 'item'},
              {'item_id': 'faqeb0aLJ2QyH-mAmpvXvQ',
               'asset': 'RECIPE_Masterworks_Imbued_Granite_Maul_Head',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': '5w9g20bEi7JOkBSEq29Mlg',
               'asset': 'RECIPE_Masterworks_Imbued_Leather_Wrappings',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'V1MH_0y8hb0teJuGxcSXfw',
               'asset': 'RECIPE_Masterworks_Ornate_Maul_Handle',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'HZaxd0qJZ4lENGqsbSTudg',
               'asset': 'RECIPE_Masterworks_Hammer_GraniteMaul',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Investigate the secrets hidden below '
                                    "Ashien's Watch.",
                      'Objective2': "Find someone near Ashien's Watch that can "
                                    'translate ancient dwarvish. ',
                      'Objective3': "Bring the blueprint to Doric in Ashien's "
                                    'Watch.'}},
 {'quest_id': 'xsgOzUS-M2iCLDe-XTDq3w',
  'asset': 'Quest_Heartstrings',
  'name': 'Heartstrings',
  'description': "Follow an elven bard's trail of memory, and discover a "
                 'harmonious weapon.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'FK7SwEPmPfVFztSXScvKQA',
               'asset': 'ITEM_Shortbow_CrystalBow',
               'count': 1,
               'type': 'item'},
              {'item_id': 'PLs7nElfZHJ-5My0-SL46A',
               'asset': 'RECIPE_Weapon_Shortbow_CrystalBow',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['follow the blue-leafed trees'],
  'objective_texts': {'follow the blue-leafed trees': 'Follow the memorial '
                                                      'path, look for blue '
                                                      'trees heading toward '
                                                      'the east of Ghornfell '
                                                      'and the memorial '
                                                      'markers.'}},
 {'quest_id': 'jP8SfEP3QLjisgaHyBzCPw',
  'asset': 'Quest_HighlightingTheProblem',
  'name': 'Highlighting the Problem',
  'description': 'Explore the RuneCrafting Guild to discover the means to '
                 'craft a powerful magical weapon.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'fOeyp0zjMg8r0SmgPEbpZA',
               'asset': 'RECIPE_Weapon_Staff_StaffOfLight',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['Investigate for clues about the statue',
                 'Search the runecrafting guild for wizard statue',
                 'Charge the orb',
                 'Return to statue'],
  'objective_texts': {'Investigate for clues about the statue': 'Investigate '
                                                                'the area for '
                                                                'clues about '
                                                                'the statue.',
                      'Search the runecrafting guild for wizard statue': 'Search '
                                                                         'the '
                                                                         'Runecrafting '
                                                                         'Guild '
                                                                         'for '
                                                                         'a '
                                                                         'statue.',
                      'Charge the orb': 'Find a way to charge the  mysterious '
                                        'orb.',
                      'Return to statue': 'Return to the wizard statue.'}},
 {'quest_id': '4kbEAUJrs6mebhGkzFQxmA',
  'asset': 'Quest_FH_LettersForTheDead',
  'name': 'Letters For The Dead',
  'description': 'Postie Pete needs some help finding and delivering some '
                 'stolen letters around Bleakfields Valley in Fellhollow.',
  'category': 'side',
  'region': None,
  'rewards': [],
  'objectives': ['ObjectiveOne',
                 'ObjectiveTwo',
                 'ObjectiveThree',
                 'ObjectiveReturn',
                 'ObjectiveZero'],
  'objective_texts': {'ObjectiveOne': 'Find and deliver letters for Postie '
                                      'Pete. 0/3',
                      'ObjectiveTwo': 'Find and deliver letters for Postie '
                                      'Pete. 1/3',
                      'ObjectiveThree': 'Find and deliver letters for Postie '
                                        'Pete. 2/3',
                      'ObjectiveReturn': 'Return to Postie Pete.',
                      'ObjectiveZero': 'Visit Postie Pete near the entrance to '
                                       'Fellhollow to begin searching for lost '
                                       'letters.'}},
 {'quest_id': 'NjeUO0TBeyQGzSCmu2b3bA',
  'asset': 'Quest_UMS_MappingTheSands',
  'name': 'Mapping the Sands I',
  'description': 'Discover Moon Sprites on top of tall locations around the '
                 'Alcarrid Camp to map the Umbral Sands.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': '5llkxkJl1yTlLWO2yyxvaA',
               'asset': 'RECIPE_Armour_T0_Cape_Menaphite_Blue',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': '9dvMDEcOq6Jy42qsGD_BhQ',
               'asset': 'ITEM_Cape_MenaphiteCape_Blue',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1', 'Objective2', '0/3', '1/3', '2/3', '3/3'],
  'objective_texts': {'Objective1': 'Climb tall locations around the Alcarrid '
                                    'Camp and find their Moon Sprites',
                      'Objective2': 'Return to the Moon Sprite Shaman in the '
                                    'Alcarrid Camp',
                      '0/3': 'Climb tall locations near Alcarrid Camp and find '
                             'their Moon Sprites (0/3)',
                      '1/3': 'Climb tall locations near Alcarrid Camp and find '
                             'their Moon Sprites (1/3)',
                      '2/3': 'Climb tall locations near Alcarrid Camp and find '
                             'their Moon Sprites (2/3)',
                      '3/3': 'Climb tall locations near Alcarrid Camp and find '
                             'their Moon Sprites (3/3)'}},
 {'quest_id': 'rI4VkUT_8837ayKcLgxWwQ',
  'asset': 'Quest_UMS_MappingTheSands2',
  'name': 'Mapping the Sands II',
  'description': 'Discover Moon Sprites on top of tall locations around all of '
                 'the Umbral Sands.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'FQJHiEXl-tOLqY6GZ4Reww',
               'asset': 'RECIPE_Weapon_Longbow_BowofElidnis',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['Objective1',
                 'Objective2',
                 '0/8',
                 '1/8',
                 '2/8',
                 '3/8',
                 '4/8',
                 '5/8',
                 '6/8',
                 '7/8'],
  'objective_texts': {'Objective1': 'Climb tall locations around Umbral Sands '
                                    'and find their Moon Sprites',
                      'Objective2': 'Return to the Moon Sprite Shaman in the '
                                    'Alcarrid Camp',
                      '0/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (0/8)',
                      '1/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (1/8)',
                      '2/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (2/8)',
                      '3/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (3/8)',
                      '4/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (4/8)',
                      '5/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (5/8)',
                      '6/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (6/8)',
                      '7/8': 'Climb tall locations around Umbral Sands and '
                             'find their Moon Sprites (7/8)'}},
 {'quest_id': 'nIvEyEv-kvSwgqOLc5VopQ',
  'asset': 'Quest_UmS_MainQuest1_TribeB_Task3',
  'name': 'Mark Day',
  'description': 'Stop the Uzzer tribe from making a mistake and binding '
                 "themselves to Fuzan's Mark",
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'WqpIPU7dFtswfcaDoldlYg',
               'asset': 'ITEM_Resources_Currency_Chit_Garou',
               'count': 200,
               'type': 'item'}],
  'objectives': ['ConvinceNoble.0',
                 'ConvinceNoble.1',
                 'ConvinceNoble.2',
                 'ReturnToShangruuh'],
  'objective_texts': {'ConvinceNoble.0': 'Convince the Uzzer councillors to '
                                         'abandon the Mark Day Festival. 0/3',
                      'ConvinceNoble.1': 'Convince the Uzzer councillors to '
                                         'abandon the Mark Day Festival. 1/3',
                      'ConvinceNoble.2': 'Convince the Uzzer councillors to '
                                         'abandon the Mark Day Festival. 2/3',
                      'ReturnToShangruuh': 'Return to Shangruuh - Garou Envoy '
                                           'in the Uzzer Camp'}},
 {'quest_id': 'KLBpt02O2AA_kaa_A8Av9w',
  'asset': 'Quest_FH_MirrorMirror',
  'name': 'Mirror Mirror',
  'description': 'Help free a mysterious figure from their mirror prison.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': '5Y972kmdvcs4vSqWaXZltw',
               'asset': 'ITEM_Longbow_Ulvs',
               'count': 1,
               'type': 'item'},
              {'item_id': 'tAXLpEJbsN7MqbW6YdwGfQ',
               'asset': 'RECIPE_Weapon_Longbow_Ulvs',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['FindSilverThread', 'LightCandles', 'ReturnToNPC'],
  'objective_texts': {'FindSilverThread': 'Gather dragon blood, spectral '
                                          'silver thread and a ritual '
                                          'spellbook and bring them back to '
                                          'the mirror.',
                      'LightCandles': 'Rekindle the memorial candles across '
                                      'Ashenfall.',
                      'ReturnToNPC': 'Speak to the mirror.'}},
 {'quest_id': '1BhNkkkP6y7ireu6yVR5tg',
  'asset': 'Quest_UmS_MainQuest1_TribeA_Task1',
  'name': 'Rag and Bone Garou',
  'description': 'Bring materials to Lagra - The Butcher in the Alcarrid '
                 'Camp. ',
  'category': 'side',
  'region': None,
  'rewards': [],
  'objectives': ['GatherIngredients'],
  'objective_texts': {'GatherIngredients': 'Bring Lagra - The Butcher 3 raw '
                                           'farm meat, 3 kalphite shell '
                                           'fragments and 3 cactus steaks'}},
 {'quest_id': 'eKV5vkDqZH89aGWiY_T7GQ',
  'asset': 'Quest_RestlessGhosts',
  'name': 'Restless Ghosts',
  'description': 'Lay to rest the spirits of the lost expedition members.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'R9IjjUjvqfnoc3ml3yyurg',
               'asset': 'ITEM_Consumable_RestlessGhostsPack',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Found ghost amulet', 'Put ghosts to rest'],
  'objective_texts': {'Found ghost amulet': 'Search for a purpose for the '
                                            'Amulet of Ghostspeak.',
                      'Put ghosts to rest': 'Find the restless spirits and '
                                            'help lay them to rest. They only '
                                            'appear at night. '}},
 {'quest_id': 'd6s4dUyoCduLy7eRc2KndQ',
  'asset': 'Quest_UmS_MainQuest1_TribeA_Task2',
  'name': 'Rogue Trader',
  'description': 'Domri - The Merchant is looking for 3 moonstones for their '
                 'shop',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'WqpIPU7dFtswfcaDoldlYg',
               'asset': 'ITEM_Resources_Currency_Chit_Garou',
               'count': 200,
               'type': 'item'}],
  'objectives': ['FindMoonstone', 'ReturnToShopkeeper'],
  'objective_texts': {'FindMoonstone': 'Find 3 moonstones beneath gypsum '
                                       'deposits in rocky areas west of '
                                       'Alcarrid',
                      'ReturnToShopkeeper': 'Return to Domri - The Merchant in '
                                            'the Alcarrid Camp'}},
 {'quest_id': 'XElCtUmXXqK35p63tua9og',
  'asset': 'Quest_UmS_MainQuest1_TribeB_Task1',
  'name': 'Saga of the Adventurer',
  'description': 'Help Laguna - The Bard to find stone slabs in rocky spires '
                 'around the pyramid',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'RUF3fEDcbPT288-vcymy0Q',
               'asset': 'ITEM_Resources_Key_NC_UmS_04',
               'count': 1,
               'type': 'item'}],
  'objectives': ['FindTheClues',
                 'None',
                 'FindRemainingClues2/4',
                 'FindRemainingClues3/4',
                 'LocateTheGateway',
                 'ReturnToBard'],
  'objective_texts': {'FindTheClues': 'Use your Saga to find clues towards the '
                                      'treasure',
                      'None': 'Continue to find stone slabs. Your Saga has '
                              'been updated!',
                      'FindRemainingClues2/4': 'Continue to find stone slabs. '
                                               'Your Saga has been updated!',
                      'FindRemainingClues3/4': 'Continue to find stone slabs. '
                                               'Your Saga has been updated!',
                      'LocateTheGateway': 'Follow the final clue to the last '
                                          'stone slab. Your Saga has been '
                                          'updated! ',
                      'ReturnToBard': 'Return to Laguna - The Bard'}},
 {'quest_id': 'Bnon4kzm_EdvZz-bma5HBg',
  'asset': 'Quest_UmS_MainQuest1_TribeC_Task2',
  'name': 'Scaling Difficulties',
  'description': 'Find some lost garou scouts and slay the creature they have '
                 'been tracking',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'WqpIPU7dFtswfcaDoldlYg',
               'asset': 'ITEM_Resources_Currency_Chit_Garou',
               'count': 200,
               'type': 'item'}],
  'objectives': ['FindDragon', 'SearchLocation', 'ReturnToGarou'],
  'objective_texts': {'FindDragon': 'Locate the dragon to the east and bring '
                                    'its heart back to Hedric - The Hunter',
                      'SearchLocation': 'Search the village to the east for '
                                        'signs of the lost scouts',
                      'ReturnToGarou': 'Return the dragon heart to Hedric - '
                                       'The Hunter'}},
 {'quest_id': 'kTD_70L2tJmsOiSW5iCYVw',
  'asset': 'Quest_ScarecrowScavenging',
  'name': 'Scarecrow Scavenging',
  'description': '',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'lp2zMkifzBWtPlO2fwl2AA',
               'asset': 'RECIPE_Armour_T2_Head_FarmersHat',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'eBbNtkOP-XJvtcSF24kCQQ',
               'asset': 'ITEM_Consumable_ScarecrowScavenging',
               'count': 1,
               'type': 'item'}],
  'objectives': [],
  'objective_texts': {}},
 {'quest_id': 'Rov9uE687b2NkaKFCTFP3A',
  'asset': 'Quest_FH_WitherWard',
  'name': 'Seeking Salvation',
  'description': 'Find the statues to gain entrance to the vault and uncover '
                 'the secrets that lie within. ',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'f_tlM0y-QfSP8Ha6vD6Rmg',
               'asset': 'ITEM_Resources_Salve_Crystal',
               'count': 1,
               'type': 'item'},
              {'item_id': 'SboNX0qCD6PDVoWSj8UZHw',
               'asset': 'RECIPE_Trinket_Salve_Amulet',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['FindRecipe', 'ReturnToDoric', 'LookForDoric'],
  'objective_texts': {'FindRecipe': 'Access the vault and find the hidden '
                                    'secret within. ',
                      'ReturnToDoric': 'Bring the dwarven writing to Doric. ',
                      'LookForDoric': 'Find someone in Fellhollow that can '
                                      'translate dwarvish text. '}},
 {'quest_id': 'Xb1KUkU_wOIHvzahULr6yA',
  'asset': 'Quest_UmS_MainQuest1_TribeC_Task3',
  'name': 'Song of the Ancients',
  'description': "Complete the 'Song of the Ancients' by finding lyrics on "
                 'stone slabs within the Dragonkin Vault.',
  'category': 'side',
  'region': None,
  'rewards': [],
  'objectives': ['FindStatues.0',
                 'FindStatues.1',
                 'FindStatues.2',
                 'FindStatues.3',
                 'FindStatues.4',
                 'Return'],
  'objective_texts': {'FindStatues.0': 'Transcribe lyrics written on stone '
                                       'slabs within the Dragonkin Vault. 0/3',
                      'FindStatues.1': 'Transcribe lyrics written on stone '
                                       'slabs within the Dragonkin Vault. 1/3',
                      'FindStatues.2': 'Transcribe lyrics written on stone '
                                       'slabs within the Dragonkin Vault. 2/3',
                      'FindStatues.3': None,
                      'FindStatues.4': None,
                      'Return': 'Return to Laguna - The Bard in the Manafem '
                                'Camp. '}},
 {'quest_id': '8Rb0t0upslwKHXWYGnTKgg',
  'asset': 'Quest_UmS_MainQuest1_TribeB_Task2',
  'name': 'The Dig Site',
  'description': 'Dig up buried history in garou ruins far to the south',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'WqpIPU7dFtswfcaDoldlYg',
               'asset': 'ITEM_Resources_Currency_Chit_Garou',
               'count': 200,
               'type': 'item'}],
  'objectives': ['DigScroll.0',
                 'DigScroll.1',
                 'DigScroll.2',
                 'DigScroll.3',
                 'ReturnToArchaeologist'],
  'objective_texts': {'DigScroll.0': 'Dig up Forbidden Scrolls in the garou '
                                     'ruins. 0/4',
                      'DigScroll.1': 'Dig up Forbidden Scrolls in the garou '
                                     'ruins. 1/4',
                      'DigScroll.2': 'Dig up Forbidden Scrolls in the garou '
                                     'ruins. 2/4',
                      'DigScroll.3': 'Dig up Forbidden Scrolls in the garou '
                                     'ruins. 3/4',
                      'ReturnToArchaeologist': 'Return to Lehran - The '
                                               'Archaeologist in the Uzzer '
                                               'Camp'}},
 {'quest_id': 'db-ciknQnYrkNHuOcQXhkA',
  'asset': 'Quest_GreatBodyRobbery',
  'name': 'The Great Body Robbery',
  'description': 'Assist Dr Fenkenstrain in acquiring a new body. FOR SCIENCE!',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': '-fbjZE8aCAERg0-TuBMRcg',
               'asset': 'RECIPE_Weapon_T4_Club_ZombieArm',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'ZUMRukFLXvSUBtSY_HzEPA',
               'asset': 'ITEM_Mace_ZombieClub',
               'count': 1,
               'type': 'item'}],
  'objectives': ['BodyParts.0',
                 'Objective2',
                 'Objective3',
                 'Objective4',
                 'Objective5',
                 'Objecrive3.5',
                 'Objective6',
                 'Objective7',
                 'Objective8',
                 'Objective9',
                 'BodyParts.1',
                 'BodyParts.2',
                 'AddPartsToTable'],
  'objective_texts': {'BodyParts.0': 'Dig up body parts from graves around '
                                     'Bloodblight Swamp. 0/3',
                      'Objective2': 'Speak to Fenkenstrain',
                      'Objective3': 'Speak to Fenkenstrain',
                      'Objective4': 'Bring Dr Fenkenstrain: 1 Weak Antipoison, '
                                    '1 Weak Focused Attack Potion and 1 Weak '
                                    'Lumberjack Potion.',
                      'Objective5': 'Collect lightning in a bottle and bring '
                                    'it to Dr Fenkenstrain.',
                      'Objecrive3.5': 'Perform an autopsy of the body on the '
                                      'examination table in Doctor '
                                      "Fenkenstrain's tower. ",
                      'Objective6': 'Speak to Fenkenstrain',
                      'Objective7': "Put Doctor Fenkenstrain's head on his new "
                                    'body on the examination table. ',
                      'Objective8': 'Put the Lightning-in-a-bottle into the '
                                    "machine in Doctor Fenkenstrain's lab. ",
                      'Objective9': 'Speak to Fenkenstrain',
                      'BodyParts.1': 'Dig up body parts from graves around '
                                     'Bloodblight Swamp. 1/3',
                      'BodyParts.2': 'Dig up body parts from graves around '
                                     'Bloodblight Swamp. 2/3',
                      'AddPartsToTable': 'Place the body parts on the '
                                         "examination table in Fenkenstrain's "
                                         'tower.'}},
 {'quest_id': 'd6M5Dkpx9Pjw_V2mNJh6eA',
  'asset': 'Quest_UmS_MainQuest1_TribeA_Task3',
  'name': "The Mirror Crack'd",
  'description': 'Valas - The Blacksmith is looking for some adamant bars to '
                 'repair the Mirror Relay',
  'category': 'side',
  'region': None,
  'rewards': [],
  'objectives': ['BringBars'],
  'objective_texts': {'BringBars': 'Bring Valas - The Blacksmith 3 adamant '
                                   'bars'}},
 {'quest_id': 'rai6k0UuXT_GPEixJM0boQ',
  'asset': 'Quest_FH_WitherBeast',
  'name': 'The Wild Hunt',
  'description': "Help Vannaka safeguard Fellhollow's nature spirits, by "
                 'hunting them down, in willow groves, and collecting their '
                 'hearts. ',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': None,
               'asset': 'DA_Mount_Terrorbird_00_00',
               'count': 1,
               'type': 'mount_unlock'}],
  'objectives': ['HuntBeast', 'BringHeart', 'BringHeartNotStarted'],
  'objective_texts': {'HuntBeast': "Hunt down Nature Spirits near Fellhollow's "
                                   'willow groves and bring three of their '
                                   'hearts to Vannaka. ',
                      'BringHeart': 'Bring the hearts to Vannaka. ',
                      'BringHeartNotStarted': 'Bring the Primordial Heart to '
                                              'someone with an interest in the '
                                              'wild hunt. '}},
 {'quest_id': 'wwEK50EPipTecO20yTquSQ',
  'asset': 'Quest_FH_NightoftheSpectralBoom',
  'name': 'Things That Go Boom In The Night',
  'description': 'Gather spectral chinchompa skulls so that Vannaka can help '
                 'the land heal. ',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'nFRdHU7L4A3xRjOWjzMzoQ',
               'asset': 'RECIPE_Armour_T0_Cape_Chinchompa',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'uqGAn0tZnBkZEJSwmx70KA',
               'asset': 'ITEM_Cape_Chinchompa',
               'count': 1,
               'type': 'item'}],
  'objectives': ['FindSpectralChinchompaSkulls', 'SpeaktoVannaka'],
  'objective_texts': {'FindSpectralChinchompaSkulls': 'Gather 10 spectral '
                                                      'chinchompa skulls and '
                                                      'bring them to Vannaka '
                                                      'in Fellhollow.',
                      'SpeaktoVannaka': 'Speak to Vannaka in Fellhollow.'}},
 {'quest_id': '9Kod2UgSkm8YrJCwMgmAdQ',
  'asset': 'Quest_SQ2_AnimalLover',
  'name': 'Wanted!',
  'description': 'Hunt down the Beast Tamers',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'yNesKEC_bp6SYxajG0nAOA',
               'asset': 'RECIPE_Trinket_Unholy_Symbol',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['DR_SQ2_EntryJournal',
                 'DR_SQ2_FindPages_0',
                 'DR_SQ2_FindPages_1',
                 'DR_SQ2_FindPages_2',
                 'DR_SQ2_ReturnToVannaka'],
  'objective_texts': {'DR_SQ2_EntryJournal': 'Bring the Journal to Vannaka',
                      'DR_SQ2_FindPages_0': 'Journal Pages Collected 0/3',
                      'DR_SQ2_FindPages_1': 'Journal Pages Collected 1/3',
                      'DR_SQ2_FindPages_2': 'Journal Pages Collected 2/3',
                      'DR_SQ2_ReturnToVannaka': 'Journal Pages Collected '
                                                '3/3\r\n'
                                                'Return to Vannaka'}},
 {'quest_id': 'WXRGL036pJRhAU-BWTZ_9g',
  'asset': 'Quest_FH_WhatRemainsIsWritten',
  'name': 'What Remains is Written',
  'description': "Find stolen knowledge and return it to its owner. I'm sure "
                 'nothing bad will happen because of it.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'a5xW8kOqRN0fi6iIKloioA',
               'asset': 'RECIPE_Trinket_Runic_Ring',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'TuG7zUS90qgd7BOHhOxd8Q',
               'asset': 'ITEM_Trinket_Iconic_Runic_Ring',
               'count': 1,
               'type': 'item'}],
  'objectives': ['FindBooks',
                 'FoundBooks',
                 'FindScrolls',
                 'FoundScrolls',
                 'FindBooksAndReturn',
                 'FindScrollsAndReturn',
                 'ObjectiveZero'],
  'objective_texts': {'FindBooks': 'Find five of Abraxus’ missing books in '
                                   'eastern Fellhollow and return them to him.',
                      'FoundBooks': 'Bring the books to Abraxus.',
                      'FindScrolls': "Defeat Abraxus' enemies to retrieve the "
                                     'scrolls.',
                      'FoundScrolls': 'Bring the scrolls to Abraxus.',
                      'FindBooksAndReturn': 'Find five of Abraxus’ missing '
                                            'books in eastern Fellhollow and '
                                            'return them to him.',
                      'FindScrollsAndReturn': "Defeat Abraxus' enemies to "
                                              'retrieve the scrolls. Then '
                                              'return them to Abraxus.',
                      'ObjectiveZero': 'Find the owner of the sinister '
                                       'text. '}},
 {'quest_id': 'vxS7_kzdpGvmWKWwjqF7Jg',
  'asset': 'Quest_SQ1_ThinkingWithPortals',
  'name': "What's Theirs is Mine",
  'description': 'Help Doric track down the mage that stole his keepsake, by '
                 'unlocking portals around Dowdun Reach.',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'pv95S0brp1asAqiI64g9Ig',
               'asset': 'RECIPE_Masterwork_Weapon_Staff_Zamorak',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': ['DR_SQ1_Temple',
                 'DR_SQ1_Garrison',
                 'DR_SQ1_Aquifer',
                 'DR_SQ1_ReturnToDoric'],
  'objective_texts': {'DR_SQ1_Temple': 'Look for signs of the mugger-mage in '
                                       'the Cathedral in Dowdun Keep.',
                      'DR_SQ1_Garrison': 'Look for signs of the mugger-mage in '
                                         'the Garrisons of Dowdun Keep.',
                      'DR_SQ1_Aquifer': 'Look for signs of the mugger-mage in '
                                        'the underground Demon Gate of Dowdun '
                                        'Keep.',
                      'DR_SQ1_ReturnToDoric': 'Speak to Doric in the Dowdun '
                                              'Reach Nexus.'}},
 {'quest_id': 'xmM520wY0W5Qw8qE3YnC5Q',
  'asset': 'Quest_Whip',
  'name': 'Whip',
  'description': '',
  'category': 'side',
  'region': None,
  'rewards': [{'item_id': 'kRJ8QUBQGTMmDROOrE_OnQ',
               'asset': 'RECIPE_Masterworks_Club_AbyssalWhip',
               'count': 1,
               'type': 'recipe_unlock'}],
  'objectives': [],
  'objective_texts': {}},
 {'quest_id': 'luaLQEzPXjx9_ICiz5zkNg',
  'asset': 'Quest_FTUE_FS',
  'name': 'First Steps',
  'description': 'Begin your adventure.',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': 'U6OtnkxHtcHAIPy1kMGc8A',
               'asset': 'ITEM_Consumable_Tome_Tier1_Runecrafting',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1'],
  'objective_texts': {'Objective1': 'Speak to the Wise Old Man in Bramblemead '
                                    'village.'}},
 {'quest_id': 'AmuXOUitB08PYDCmdVA_Ug',
  'asset': 'Quest_FTUE_GS',
  'name': 'First Steps',
  'description': 'Begin your adventure.',
  'category': 'tutorial',
  'region': None,
  'rewards': [],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Speak to the Wise Old Man in the Temple.',
                      'Objective2': 'Speak to the Wise Old Man in the Temple.',
                      'Objective3': 'Speak to Doric outside the Temple.'}},
 {'quest_id': 'v9LCTEjS-igQFrq4bpvtsA',
  'asset': 'Quest_FTUE_Q1',
  'name': 'First Steps',
  'description': 'Begin your adventure. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Speak to the Wise Old Man in the Temple.',
                      'Objective2': 'Speak to the Wise Old Man in the Temple.',
                      'Objective3': 'Speak to Doric outside the Temple.'}},
 {'quest_id': '7i8X403LNgw6uY-XK5OgnA',
  'asset': 'Quest_FTUE_Q7',
  'name': 'First Steps',
  'description': 'Begin your adventure. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [],
  'objectives': ['Objective1'],
  'objective_texts': {'Objective1': 'Speak to the Wise Old Man in the '
                                    'Temple.'}},
 {'quest_id': 'xa8o60AbJZ23FymQeiH3bg',
  'asset': 'Quest_FTUE_RtftJ',
  'name': 'Getting Started',
  'description': 'Doric wants to teach you some survival basics. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': 'lUXT6k3qLQtJa4CdnnJw5g',
               'asset': 'ITEM_Consumable_Soup_Vegetable',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Collect some dirty water from the nearby '
                                    'ponds and bring them back to Doric.',
                      'Objective2': 'Build a crafting table and craft a stone '
                                    'club, then bring it to Doric.',
                      'Objective3': 'Bring the stone club to Doric outside the '
                                    'temple.'}},
 {'quest_id': '_L6IAEaHSVPnhhaTamBHBA',
  'asset': 'Quest_FTUE_Farming',
  'name': 'Growing Pains',
  'description': 'Learn the basics of the Farming skill from the Wise Old '
                 'Man. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': 'RcJw8Ede_CIqdmSZCv-D2A',
               'asset': 'ITEM_Consumable_FinishedFarmingTutorialPack',
               'count': 1,
               'type': 'item'}],
  'objectives': ['SpeakToWOM1',
                 'BuildGardenPlot',
                 'PlantSeeds',
                 'SpeakToWOM2',
                 'FullyWaterPlot',
                 'HarvestPlot',
                 'SpeakToWOM3',
                 'GetCompost',
                 'ApplyCompostToPlot',
                 'FinishQuest',
                 'HarvestCrop'],
  'objective_texts': {'SpeakToWOM1': 'Speak to the Wise Old Man, in '
                                     'Bramblemead, to learn about the Farming '
                                     'skill. ',
                      'BuildGardenPlot': '[TEMP] Build a Garden Plot',
                      'PlantSeeds': '[TEMP] Plant Wheat Seeds',
                      'SpeakToWOM2': '[TEMP] Speak to the Wise Old Man to '
                                     'learn about watering and harvesting',
                      'FullyWaterPlot': '[TEMP] Fully water a Gardening Plot',
                      'HarvestPlot': '[TEMP] Harvest Wheat at a Gardening Plot',
                      'SpeakToWOM3': '[TEMP] Return to the Wise Old Man',
                      'GetCompost': '[TEMP] Obtain compost from a compost bin',
                      'ApplyCompostToPlot': '[TEMP] Fully treat Garden Plot '
                                            'with compost',
                      'FinishQuest': 'Return to the Wise Old Man in '
                                     'Bramblemead.',
                      'HarvestCrop': 'Grow and harvest your first crop from a '
                                     'farming plot. '}},
 {'quest_id': '4lW6rU0i0js1e3qFEAVI4w',
  'asset': 'Quest_FTUE_Q5',
  'name': 'Ratcatcher',
  'description': 'Vannaka wants you to prove yourself in combat. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [],
  'objectives': ['Objective1', 'Objective2'],
  'objective_texts': {'Objective1': 'Speak to Vannaka.',
                      'Objective2': 'Bring 3 small animal fangs to Vannaka'}},
 {'quest_id': 'SDcUrkVqRiTKKEyzEh5DWw',
  'asset': 'Quest_FTUE_RC',
  'name': 'Ratcatcher',
  'description': 'Vannaka wants to teach you the basics of hunting, fighting '
                 'and cooking. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': '0NWm0hwPokOAgp0ux3ambA',
               'asset': 'ITEM_Logging_Axe_Stone',
               'count': 1,
               'type': 'item'},
              {'item_id': 'f5pdM9IkUU2dZp0okjecuA',
               'asset': 'ITEM_Dagger_Stone',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Objective1', 'Objective2'],
  'objective_texts': {'Objective1': 'Speak to Vannaka near the Windmill.',
                      'Objective2': 'Kill rats and successfully cook one rat '
                                    'roast from their meat.'}},
 {'quest_id': 'YTzYzUk_2vcK4RSEwe-m3w',
  'asset': 'Quest_FTUE_Q2',
  'name': 'Right Tool for the Job',
  'description': 'Doric wants to teach you the fundamentals. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': 'lCE7i3iXGUuHv7FphIOcXg',
               'asset': 'ITEM_Rune_Earth',
               'count': 25,
               'type': 'item'},
              {'item_id': '4wdYZE-FFMhS9Iia0ftWDg',
               'asset': 'ITEM_Rune_Astral',
               'count': 25,
               'type': 'item'},
              {'item_id': '_QMgbMYhjU-9jAD_euFbyQ',
               'asset': 'ITEM_Rune_Fire',
               'count': 25,
               'type': 'item'}],
  'objectives': ['Objective2', 'Objective3'],
  'objective_texts': {'Objective2': 'Craft a stone logging axe at a workbench '
                                    'and show it to Doric. ',
                      'Objective3': 'Return to Doric and show him the stone '
                                    'logging axe. '}},
 {'quest_id': 'TgVnb0NCLvmEVRed59IgsQ',
  'asset': 'Quest_FTUE_LO',
  'name': 'Rune Mysteries',
  'description': 'Zanik wants you to learn the basics of crafting runes.',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': 'BcoOLIbLs0SLeM3EhJJXSw',
               'asset': 'ITEM_Pickaxe_Stone',
               'count': 1,
               'type': 'item'}],
  'objectives': ['Speak to Zanik', 'Chop wood'],
  'objective_texts': {'Speak to Zanik': 'Speak to Zanik, near the river down '
                                        'the road from the temple.',
                      'Chop wood': 'Bring 50 ash logs to Zanik.'}},
 {'quest_id': 'EWRW7Ux-jHohLEKQCrkJJw',
  'asset': 'Quest_FTUE_Q4',
  'name': 'Rune Mysteries',
  'description': 'Learn the basics of crafting runes. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Speak to the Wise Old Man in the temple.',
                      'Objective2': 'Mine rune essence, build a rune altar and '
                                    'craft some air runes.',
                      'Objective3': 'Speak to the Wise Old Man in the '
                                    'temple.'}},
 {'quest_id': 'zrqqFUNmx3lcF6umysJfvQ',
  'asset': 'Quest_FTUE_RM',
  'name': 'Rune Mysteries',
  'description': 'Zanik wants you to learn the basics of crafting runes.',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': '1lnRvU1YsQeoDdyR_9s6Ug',
               'asset': 'ITEM_Consumable_Tome_Tier1_Woodcutting',
               'count': 1,
               'type': 'item'},
              {'item_id': '4wdYZE-FFMhS9Iia0ftWDg',
               'asset': 'ITEM_Rune_Astral',
               'count': 10,
               'type': 'item'},
              {'item_id': 'Dvo6TE2d7YNnoni8XbKYzw',
               'asset': 'ITEM_Rune_Air',
               'count': 10,
               'type': 'item'}],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Speak to Zanik near the river, down the '
                                    'road from the temple.',
                      'Objective2': 'Mine Rune Essence, craft some Air and '
                                    'Astral Runes by building a Rune Altar or '
                                    'from Siphoning Anima Vents.',
                      'Objective3': 'Return to Zanik.'}},
 {'quest_id': '_8zxGkuJtgJeZgG_lEGXuw',
  'asset': 'Quest_FTUE_Q3',
  'name': 'Seeking Shelter',
  'description': 'Zanik wants to teach you some survival basics.',
  'category': 'tutorial',
  'region': None,
  'rewards': [],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Speak to Zanik.',
                      'Objective2': 'Build and then claim a bed. ',
                      'Objective3': 'Speak to Zanik.'}},
 {'quest_id': '8gKiWUPU3vW2sQesVHdrPA',
  'asset': 'Quest_DR_FTUE_Fishing',
  'name': 'Shrimp Catcher',
  'description': 'The Wise Old Man has some tips on how to grow as an amateur '
                 'angler. ',
  'category': 'tutorial',
  'region': None,
  'rewards': [{'item_id': 'QwGXZE4nIZWUh2qSPgUq6g',
               'asset': 'ITEM_Consumable_Tome_Tier1_Fishing',
               'count': 1,
               'type': 'item'},
              {'item_id': 'cO_JmkaXV2sn9qyROLNgOA',
               'asset': 'ITEM_FishBait_Shrimp',
               'count': 3,
               'type': 'item'},
              {'item_id': 'h1pEpUIgboLjOJKsjXXJZw',
               'asset': 'ITEM_FishBait_Feather',
               'count': 3,
               'type': 'item'}],
  'objectives': ['SpeakToWom', 'StartFishing', 'ReturnToTheWOM'],
  'objective_texts': {'SpeakToWom': 'Speak to the Wise Old Man in Bramblemead '
                                    'Village to learn about Fishing.',
                      'StartFishing': 'Fish a Sardine at a fishing spot near '
                                      'the Wise Old Man in Bramblemead '
                                      'Village.',
                      'ReturnToTheWOM': 'Return to the Wise Old Man in '
                                        'Bramblemead Village.'}},
 {'quest_id': 'DSGuYE-gPNCI1yCzvZhT8Q',
  'asset': 'Quest_FTUE_WardStones',
  'name': 'Warding Off Danger',
  'description': 'The Wise Old Man wants to teach you about Lifewards and how '
                 'to recharge them.',
  'category': 'tutorial',
  'region': None,
  'rewards': [],
  'objectives': ['Objective1', 'Objective2', 'Objective3'],
  'objective_texts': {'Objective1': 'Speak to the Wise Old Man to learn about '
                                    'Lifewards.',
                      'Objective2': 'Craft a Small Wardstone at a Crafting '
                                    'Table and bring it to the Wise Old Man.',
                      'Objective3': 'Bring your Small Wardstone to the Wise '
                                    'Old Man.'}},
 {'quest_id': 'Nw3wiUaB8siRIN2bStWJmw',
  'asset': 'Quest_SW_MainQuest',
  'name': 'Regicide',
  'description': 'Take the fight to Kuldra, and end this once and for all. ',
  'category': 'main',
  'region': None,
  'rewards': [{'item_id': 'yPxVHUt4c8xZInC2YuTobg',
               'asset': 'RECIPE_Armour_T8_Cape_Dragonslayer',
               'count': 1,
               'type': 'recipe_unlock'},
              {'item_id': 'NfsDG0_3S4YQdcCD8_PjKA',
               'asset': 'ITEM_Consumable_KuldraPack_Unique',
               'count': 1,
               'type': 'item'}],
  'objectives': ['DefeatKuldra',
                 'BringHead',
                 'AccessSW',
                 'SpeakZilyana',
                 'ReturnToZilyana'],
  'objective_texts': {'DefeatKuldra': 'Defeat Kuldra',
                      'BringHead': "Bring Kuldra's head to Zilyana. ",
                      'AccessSW': 'Gain access to the Scorned Wilderness. ',
                      'SpeakZilyana': 'Speak to Zilyana. ',
                      'ReturnToZilyana': 'Once you are fully prepared, speak '
                                         'to Zilyana. '}}]
