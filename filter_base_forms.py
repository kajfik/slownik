#!/usr/bin/env python3
"""
Filter Polish word list to keep only base forms (lemmas):
- Verbs: keep only infinitives (ending in -ć)
- Adjectives: keep only masculine nominative singular
- Nouns: keep only nominative singular

Strategy: for each word, try to reconstruct its base form using suffix mappings.
Only remove a word if the reconstructed base form exists in the dictionary.
"""

import gzip
import sys


def build_verb_suffix_maps():
    """
    Build mappings: (conjugated_suffix, infinitive_suffix)
    If a word ends with conjugated_suffix, we try replacing it with infinitive_suffix.
    If the result exists in the dictionary, the word is a conjugated form → remove it.
    """
    maps = []

    # ===================== -ować verbs =====================
    # e.g., pracować, patetyzować
    # Present tense: stem+uję, stem+ujesz, ...
    # The mapping: replace suffix with 'ować'

    ować_suffixes = [
        # Present tense
        'uje', 'ujesz', 'ujemy', 'ujecie',
        # uję and ują handled carefully (short)
        'uję', 'ują',
        # Past tense
        'owałem', 'owałeś', 'ował', 'owała', 'owałam', 'owałaś',
        'owało', 'owaliśmy', 'owaliście', 'owali',
        'owałyśmy', 'owałyście', 'owały',
        # Conditional
        'owałbym', 'owałbyś', 'owałby',
        'owałabym', 'owałabyś', 'owałaby',
        'owałoby',
        'owalibyśmy', 'owalibyście', 'owaliby',
        'owałybyśmy', 'owałybyście', 'owałyby',
        # Imperative
        'uj', 'ujmy', 'ujcie',
        'ujże', 'ujmyż', 'ujcież',
        # Active participle (all declensions)
        'ując',
        'ujący', 'ująca', 'ujące',
        'ującego', 'ującej', 'ującemu',
        'ującym', 'ujących', 'ującymi', 'ującą',
        # Passive participle (all declensions)
        'owany', 'owana', 'owane',
        'owanego', 'owanej', 'owanemu',
        'owanym', 'owanych', 'owanymi', 'owaną',
        'owani',
        # Impersonal past
        'owano',
        # Verbal noun (all declensions)
        'owanie', 'owania', 'owaniu', 'owaniem',
        'owaniach', 'owaniami', 'owaniom', 'owań',
    ]
    for s in ować_suffixes:
        maps.append((s, 'ować'))

    # ===================== -ywać/-iwać verbs =====================
    # e.g., zapisywać, odkrywać
    ywać_suffixes = [
        'uje', 'ujesz', 'ujemy', 'ujecie', 'uję', 'ują',
        'ywałem', 'ywałeś', 'ywał', 'ywała', 'ywałam', 'ywałaś',
        'ywało', 'ywaliśmy', 'ywaliście', 'ywali',
        'ywałyśmy', 'ywałyście', 'ywały',
        'ywałbym', 'ywałbyś', 'ywałby',
        'ywałabym', 'ywałabyś', 'ywałaby',
        'ywałoby',
        'ywalibyśmy', 'ywalibyście', 'ywaliby',
        'ywałybyśmy', 'ywałybyście', 'ywałyby',
        'uj', 'ujmy', 'ujcie',
        'ujże', 'ujmyż', 'ujcież',
        'ując',
        'ujący', 'ująca', 'ujące',
        'ującego', 'ującej', 'ującemu',
        'ującym', 'ujących', 'ującymi', 'ującą',
        'ywany', 'ywana', 'ywane',
        'ywanego', 'ywanej', 'ywanemu',
        'ywanym', 'ywanych', 'ywanymi', 'ywaną',
        'ywani',
        'ywano',
        'ywanie', 'ywania', 'ywaniu', 'ywaniem',
        'ywaniach', 'ywaniami', 'ywaniom', 'ywań',
    ]
    for s in ywać_suffixes:
        maps.append((s, 'ywać'))

    iwać_suffixes = [s.replace('yw', 'iw') for s in ywać_suffixes if 'yw' in s]
    for s in iwać_suffixes:
        maps.append((s, 'iwać'))

    # ===================== -ać verbs (conjugation I: -am/-asz) =====================
    # e.g., czytać, kochać, grać, latać
    ać_suffixes = [
        # Present tense (short, but we include them)
        'am', 'asz', 'amy', 'acie', 'ają',
        # Past tense
        'ałem', 'ałeś', 'ał', 'ała', 'ałam', 'ałaś',
        'ało', 'aliśmy', 'aliście', 'ali',
        'ałyśmy', 'ałyście', 'ały',
        # Conditional
        'ałbym', 'ałbyś', 'ałby',
        'ałabym', 'ałabyś', 'ałaby',
        'ałoby',
        'alibyśmy', 'alibyście', 'aliby',
        'ałybyśmy', 'ałybyście', 'ałyby',
        # Imperative
        'aj', 'ajmy', 'ajcie',
        'ajże', 'ajmyż', 'ajcież',
        # Active participle
        'ając',
        'ający', 'ająca', 'ające',
        'ającego', 'ającej', 'ającemu',
        'ającym', 'ających', 'ającymi', 'ającą',
        # Passive participle
        'any', 'ana', 'ane',
        'anego', 'anej', 'anemu',
        'anym', 'anych', 'anymi', 'aną',
        'ani',
        # Impersonal past
        'ano',
        # Verbal noun
        'anie', 'ania', 'aniu', 'aniem',
        'aniach', 'aniami', 'aniom', 'ań',
    ]
    for s in ać_suffixes:
        maps.append((s, 'ać'))

    # ===================== -ić verbs =====================
    # e.g., robić, prosić, chodzić
    ić_suffixes = [
        # Present tense
        'ię', 'isz', 'imy', 'icie', 'ią',
        # Past tense
        'iłem', 'iłeś', 'ił', 'iła', 'iłam', 'iłaś',
        'iło', 'iliśmy', 'iliście', 'ili',
        'iłyśmy', 'iłyście', 'iły',
        # Conditional
        'iłbym', 'iłbyś', 'iłby',
        'iłabym', 'iłabyś', 'iłaby',
        'iłoby',
        'ilibyśmy', 'ilibyście', 'iliby',
        'iłybyśmy', 'iłybyście', 'iłyby',
        # Imperative
        'ij', 'ijmy', 'ijcie',
        'ijże', 'ijmyż', 'ijcież',
        # Active participle
        'iąc',
        'iący', 'iąca', 'iące',
        'iącego', 'iącej', 'iącemu',
        'iącym', 'iących', 'iącymi', 'iącą',
        # Passive participle (-ony)
        'ony', 'ona', 'one',
        'onego', 'onej', 'onemu',
        'onym', 'onych', 'onymi', 'oną',
        'eni',
        # Passive participle (-iony)
        'iony', 'iona', 'ione',
        'ionego', 'ionej', 'ionemu',
        'ionymi', 'ionym', 'ionych', 'ioną',
        'ieni',
        # Impersonal past
        'iono',
        # Verbal noun
        'ienie', 'ienia', 'ieniu', 'ieniem',
        'ieniach', 'ieniami', 'ieniom', 'ień',
    ]
    for s in ić_suffixes:
        maps.append((s, 'ić'))

    # ===================== -yć verbs =====================
    # e.g., myć, żyć, być, kryć
    yć_suffixes = [
        # Present tense
        'yję', 'yjesz', 'yje', 'yjemy', 'yjecie', 'yją',
        # Past tense
        'yłem', 'yłeś', 'ył', 'yła', 'yłam', 'yłaś',
        'yło', 'yliśmy', 'yliście', 'yli',
        'yłyśmy', 'yłyście', 'yły',
        # Conditional
        'yłbym', 'yłbyś', 'yłby',
        'yłabym', 'yłabyś', 'yłaby',
        'yłoby',
        'ylibyśmy', 'ylibyście', 'yliby',
        'yłybyśmy', 'yłybyście', 'yłyby',
        # Imperative
        'yj', 'yjmy', 'yjcie',
        'yjże', 'yjmyż', 'yjcież',
        # Active participle
        'yjąc',
        'yjący', 'yjąca', 'yjące',
        'yjącego', 'yjącej', 'yjącemu',
        'yjącym', 'yjących', 'yjącymi', 'yjącą',
        # Passive participle
        'yty', 'yta', 'yte',
        'ytego', 'ytej', 'ytemu',
        'ytym', 'ytych', 'ytymi', 'ytą',
        'yci',
        # Impersonal past
        'yto',
        # Verbal noun
        'ycie', 'ycia', 'yciu', 'yciem',
        'yciach', 'yciami', 'yciom', 'yć',  # yć is itself infinitive, skip
    ]
    # Remove 'yć' from the list (it's the infinitive itself)
    yć_suffixes = [s for s in yć_suffixes if s != 'yć']
    for s in yć_suffixes:
        maps.append((s, 'yć'))

    # ===================== -eć verbs =====================
    # e.g., boleć, maleć (past: bolał, malał)
    eć_suffixes = [
        # Past tense with -eł- pattern (rare)
        'ełem', 'ełeś', 'eł', 'eła', 'ełam', 'ełaś',
        'eło', 'eliśmy', 'eliście', 'eli',
        'ełyśmy', 'ełyście', 'eły',
        'ełbym', 'ełbyś', 'ełby',
        'ełabym', 'ełabyś', 'ełaby',
        'ełoby',
        'elibyśmy', 'elibyście', 'eliby',
        'ełybyśmy', 'ełybyście', 'ełyby',
        # Past tense with -ał- pattern (common for -eć verbs: boleć→bolał)
        'ałem', 'ałeś', 'ał', 'ała', 'ałam', 'ałaś',
        'ało', 'ałyśmy', 'ałyście', 'ały',
        'ałbym', 'ałbyś', 'ałby',
        'ałabym', 'ałabyś', 'ałaby',
        'ałoby',
        'ałybyśmy', 'ałybyście', 'ałyby',
        # Virile plural past (boleć→boleli)
        'eliśmy', 'eliście', 'eli',
        'elibyśmy', 'elibyście', 'eliby',
        # Verbal noun
        'enie', 'enia', 'eniu', 'eniem',
        'eniach', 'eniami', 'eniom', 'eń',
    ]
    # Present tense: -eć → -eje (boleć→boleje, boleją)
    eć_present = [
        'eję', 'ejesz', 'eje', 'ejemy', 'ejecie', 'eją',
        'ej', 'ejmy', 'ejcie', 'ejże', 'ejmyż', 'ejcież',
        'ejąc', 'ejący', 'ejąca', 'ejące',
        'ejącego', 'ejącej', 'ejącemu',
        'ejącym', 'ejących', 'ejącymi', 'ejącą',
    ]
    eć_suffixes.extend(eć_present)
    for s in eć_suffixes:
        maps.append((s, 'eć'))

    # ===================== -ieć verbs =====================
    # e.g., widzieć, siedzieć, ładnieć (past: widział, siedział, ładniał)
    ieć_suffixes = [
        # Past tense: -ieć → -iał (widzieć→widział, ładnieć→ładniał)
        'iałem', 'iałeś', 'iał', 'iała', 'iałam', 'iałaś',
        'iało', 'iałyśmy', 'iałyście', 'iały',
        'iałbym', 'iałbyś', 'iałby',
        'iałabym', 'iałabyś', 'iałaby',
        'iałoby',
        'iałybyśmy', 'iałybyście', 'iałyby',
        # Virile plural past (widzieć→widzieli)
        'ieliśmy', 'ieliście', 'ieli',
        'ielibyśmy', 'ielibyście', 'ieliby',
        # Verbal noun
        'ienie', 'ienia', 'ieniu', 'ieniem',
        'ieniach', 'ieniami', 'ieniom', 'ień',
    ]
    # Present tense: -ieć → -ieje (ładnieć→ładnieje, ładnieją)
    ieć_present = [
        'ieję', 'iejesz', 'ieje', 'iejemy', 'iejecie', 'ieją',
        'iej', 'iejmy', 'iejcie', 'iejże', 'iejmyż', 'iejcież',
        'iejąc', 'iejący', 'iejąca', 'iejące',
        'iejącego', 'iejącej', 'iejącemu',
        'iejącym', 'iejących', 'iejącymi', 'iejącą',
    ]
    ieć_suffixes.extend(ieć_present)
    for s in ieć_suffixes:
        maps.append((s, 'ieć'))

    # ===================== -nąć verbs =====================
    # e.g., ciągnąć, kopnąć, krzyknąć
    nąć_suffixes = [
        # Present tense
        'nę', 'niesz', 'nie', 'niemy', 'niecie', 'ną',
        # Past tense
        'nąłem', 'nąłeś', 'nął', 'nęła', 'nęłam', 'nęłaś',
        'nęło', 'nęliśmy', 'nęliście', 'nęli',
        'nęłyśmy', 'nęłyście', 'nęły',
        # Conditional
        'nąłbym', 'nąłbyś', 'nąłby',
        'nęłabym', 'nęłabyś', 'nęłaby',
        'nęłoby',
        'nęlibyśmy', 'nęlibyście', 'nęliby',
        'nęłybyśmy', 'nęłybyście', 'nęłyby',
        # Imperative
        'nij', 'nijmy', 'nijcie',
        'nijże', 'nijmyż', 'nijcież',
        # Active participle
        'nąc',  # careful - this is also infinitive-like
        # Passive participle
        'nięty', 'nięta', 'nięte',
        'niętego', 'niętej', 'niętemu',
        'niętym', 'niętych', 'niętymi', 'niętą',
        'nięci',
        # Impersonal past
        'nięto',
        # Verbal noun
        'nięcie', 'nięcia', 'nięciu', 'nięciem',
    ]
    for s in nąć_suffixes:
        maps.append((s, 'nąć'))

    # ===================== -ąć verbs (without n) =====================
    # e.g., ciąć, piąć, giąć, jąć (wziąć, zająć, etc.)
    ąć_suffixes = [
        'ąłem', 'ąłeś', 'ął', 'ęła', 'ęłam', 'ęłaś',
        'ęło', 'ęliśmy', 'ęliście', 'ęli',
        'ęłyśmy', 'ęłyście', 'ęły',
        'ąłbym', 'ąłbyś', 'ąłby',
        'ęłabym', 'ęłabyś', 'ęłaby',
        'ęłoby',
        'ęlibyśmy', 'ęlibyście', 'ęliby',
        'ęłybyśmy', 'ęłybyście', 'ęłyby',
        'ęty', 'ęta', 'ęte',
        'ętego', 'ętej', 'ętemu',
        'ętym', 'ętych', 'ętymi', 'ętą',
        'ęci',
        'ęto',
        'ęcie', 'ęcia', 'ęciu', 'ęciem',
    ]
    for s in ąć_suffixes:
        maps.append((s, 'ąć'))

    # Sort by suffix length descending (match longest first)
    maps.sort(key=lambda x: len(x[0]), reverse=True)
    return maps


def build_adjective_suffix_maps():
    """
    Build mappings for adjective declensions → base form (masc nom sg).
    """
    maps = []

    # For adjectives ending in -y (e.g., dobry, ładny, nowy)
    # Only use suffixes long enough to avoid false positives with nouns.
    # EXCLUDED: 'a','e','i','o','ą' — too short, conflicts with feminine/neuter nouns
    y_declined = [
        'ego', 'emu',  # gen/dat masc/neut
        'ym',           # instr/loc masc/neut sg, dat pl
        'ych',          # gen/loc pl
        'ymi',          # instr pl
        'ej',           # fem gen/dat/loc sg
    ]
    for s in y_declined:
        maps.append((s, 'y'))

    # For adjectives ending in -i (e.g., tani, głupi, ostatni)
    # EXCLUDED: 'ia','ie','ią' — too short, conflicts with nouns
    i_declined = [
        'iego', 'iemu',
        'im',
        'ich',
        'imi',
        'iej',
    ]
    for s in i_declined:
        maps.append((s, 'i'))

    # -ski/-cki/-dzki adjective-specific patterns (very reliable)
    ski_declined = [
        ('ska', 'ski'), ('ską', 'ski'),
        ('skich', 'ski'), ('skie', 'ski'),
        ('skiego', 'ski'), ('skiej', 'ski'),
        ('skiemu', 'ski'), ('skim', 'ski'),
        ('skimi', 'ski'), ('sko', 'ski'), ('sku', 'ski'),
        ('scy', 'ski'),  # virile plural
    ]
    maps.extend(ski_declined)

    cki_declined = [
        ('cka', 'cki'), ('cką', 'cki'),
        ('ckich', 'cki'), ('ckie', 'cki'),
        ('ckiego', 'cki'), ('ckiej', 'cki'),
        ('ckiemu', 'cki'), ('ckim', 'cki'),
        ('ckimi', 'cki'), ('cko', 'cki'), ('cku', 'cki'),
        ('ccy', 'cki'),
    ]
    maps.extend(cki_declined)

    dzki_declined = [
        ('dzka', 'dzki'), ('dzką', 'dzki'),
        ('dzkich', 'dzki'), ('dzkie', 'dzki'),
        ('dzkiego', 'dzki'), ('dzkiej', 'dzki'),
        ('dzkiemu', 'dzki'), ('dzkim', 'dzki'),
        ('dzkimi', 'dzki'), ('dzko', 'dzki'), ('dzku', 'dzki'),
        ('dzcy', 'dzki'),
    ]
    maps.extend(dzki_declined)

    # Comparative forms (-szy, -sza, -sze, etc.)
    # e.g., ładniejszy from ładny, starszy from stary
    # These are hard to map back to base, so we handle -szy declensions
    szy_declined = [
        ('sza', 'szy'), ('szą', 'szy'),
        ('sze', 'szy'), ('szego', 'szy'),
        ('szej', 'szy'), ('szemu', 'szy'),
        ('szym', 'szy'), ('szych', 'szy'),
        ('szymi', 'szy'), ('szo', 'szy'),
        ('si', 'szy'),  # virile plural
    ]
    maps.extend(szy_declined)

    # Sort by suffix length descending
    maps.sort(key=lambda x: len(x[0]), reverse=True)
    return maps


def build_noun_suffix_maps():
    """
    Build mappings for noun declensions → nominative singular.
    Only handle highly reliable patterns to avoid false positives.
    """
    maps = []

    # ===== Highly reliable patterns (long, distinctive suffixes) =====

    # -ość nouns (e.g., radość, miłość)
    maps.append(('ością', 'ość'))
    maps.append(('ości', 'ość'))
    maps.append(('ościom', 'ość'))
    maps.append(('ościami', 'ość'))
    maps.append(('ościach', 'ość'))

    # -owi (dative masc sg): domowi → dom (very distinctive)
    maps.append(('owi', ''))

    # -ów (genitive masc pl): domów → dom (very distinctive)
    maps.append(('ów', ''))

    # -ami (instrumental pl) → try multiple base endings
    maps.append(('ami', ''))   # domami → dom
    maps.append(('ami', 'a'))  # kobietami → kobieta
    maps.append(('ami', 'o'))  # miastami → miasto (rare, usually -ami for -o nouns)
    maps.append(('ami', 'e'))  # polami → pole

    # -ach (locative pl) → try multiple base endings
    maps.append(('ach', ''))   # domach → dom
    maps.append(('ach', 'a'))  # kobietach → kobieta
    maps.append(('ach', 'o'))  # miastach → miasto
    maps.append(('ach', 'e'))  # polach → pole

    # -om (dative pl) → try multiple base endings
    maps.append(('om', 'a'))  # kobietom → kobieta
    maps.append(('om', 'o'))  # miastom → miasto
    maps.append(('om', 'e'))  # polom → pole
    # NOTE: 'om' → '' skipped (too many false positives: atom, fantom, etc.)

    # -ę → -a (accusative fem sg): kobietę → kobieta
    maps.append(('ę', 'a'))

    # -ą → -a (instrumental fem sg): kobietą → kobieta
    maps.append(('ą', 'a'))

    # -em (instrumental masc/neut sg): domem → dom, problemem → problem
    maps.append(('em', ''))

    # -om (dative pl, masc base): domom → dom, kotom → kot
    maps.append(('om', ''))

    # -y → -a (gen sg / nom pl fem): kobiety → kobieta, mamy → mama
    maps.append(('y', 'a'))

    # -y → '' (nom pl masc): domy → dom, koty → kot
    maps.append(('y', ''))

    # -ie → -a (locative/dative fem): kobiecie → kobieta (stem change, rarely works)
    # Skip — stem changes make this unreliable

    # Sort by suffix length descending
    maps.sort(key=lambda x: len(x[0]), reverse=True)
    return maps


def filter_words(words):
    word_set = set(words)
    to_remove = set()

    verb_maps = build_verb_suffix_maps()
    adj_maps = build_adjective_suffix_maps()
    noun_maps = build_noun_suffix_maps()

    total = len(words)

    for idx, word in enumerate(words):
        if idx % 500000 == 0:
            print(f"  Processing: {idx:,}/{total:,} ({100*idx//total}%)", file=sys.stderr)

        if word in to_remove:
            continue

        # Skip infinitives (they are base forms for verbs)
        if word.endswith('ć'):
            continue

        found = False

        # --- Try verb mappings ---
        for suffix, inf_suffix in verb_maps:
            if word.endswith(suffix) and len(word) > len(suffix):
                stem = word[:-len(suffix)]
                if not stem:
                    continue
                infinitive = stem + inf_suffix
                if infinitive in word_set and infinitive != word:
                    to_remove.add(word)
                    found = True
                    break
        if found:
            continue

        # --- Try adjective mappings (long suffixes, safe) ---
        for suffix, base_suffix in adj_maps:
            if word.endswith(suffix) and len(word) > len(suffix):
                stem = word[:-len(suffix)]
                if not stem:
                    continue
                base = stem + base_suffix
                if base in word_set and base != word:
                    to_remove.add(word)
                    found = True
                    break
        if found:
            continue

        # --- Try short adjective suffixes with verification ---
        # These overlap with nouns, so we verify via extra declension forms.
        # e.g., "dobra" → base "dobry" exists AND "dobrego" exists → it's an adj form
        short_adj_maps = [
            ('a', 'y'), ('e', 'y'), ('o', 'y'),   # fem/neut/adverb of -y adj
            ('ą', 'y'),                             # fem instr/acc of -y adj
            ('i', 'y'),                             # virile pl of -y adj
            ('ia', 'i'), ('ie', 'i'), ('ią', 'i'),  # fem/neut/instr of -i adj
        ]
        for suffix, base_suffix in short_adj_maps:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                stem = word[:-len(suffix)]
                if not stem:
                    continue
                base = stem + base_suffix
                if base in word_set and base != word:
                    # Verify it's really an adjective by checking for other declension forms
                    if base.endswith('y'):
                        if (stem + 'ego') in word_set or (stem + 'ej') in word_set:
                            to_remove.add(word)
                            found = True
                            break
                    elif base.endswith('i'):
                        if (stem + 'iego') in word_set or (stem + 'iej') in word_set:
                            to_remove.add(word)
                            found = True
                            break
        if found:
            continue

        # --- Try noun mappings ---
        for suffix, base_suffix in noun_maps:
            if word.endswith(suffix) and len(word) > len(suffix):
                stem = word[:-len(suffix)]
                # Require minimum stem length of 3 to avoid false positives
                if len(stem) < 3:
                    continue
                # For 'y' → base mappings, protect adjective base forms
                if suffix == 'y' and len(stem) >= 3:
                    # If word looks like an adjective base form (has ego/ej forms), keep it
                    if (stem + 'ego') in word_set or (stem + 'ej') in word_set:
                        continue
                    if (stem + 'iego') in word_set or (stem + 'iej') in word_set:
                        continue
                base = stem + base_suffix
                if base in word_set and base != word:
                    to_remove.add(word)
                    found = True
                    break

    return to_remove


def main():
    print("Loading words from slowa.gz...", file=sys.stderr)
    with gzip.open('slowa.gz', 'rt', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(words):,} words.", file=sys.stderr)

    print("Filtering to base forms...", file=sys.stderr)
    to_remove = filter_words(words)
    print(f"Marked {len(to_remove):,} words for removal.", file=sys.stderr)

    filtered = [w for w in words if w not in to_remove]
    print(f"Remaining: {len(filtered):,} base forms.", file=sys.stderr)

    print("Writing slowa_base.gz...", file=sys.stderr)
    with gzip.open('slowa_base.gz', 'wt', encoding='utf-8') as f:
        f.write('\n'.join(filtered) + '\n')
    print("Done!", file=sys.stderr)


if __name__ == '__main__':
    main()
