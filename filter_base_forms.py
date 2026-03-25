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

    # -iwać: yw-suffixes converted to iw-, plus shared uj- forms (present/imperative/participle)
    iwać_suffixes = []
    for s in ywać_suffixes:
        if 'yw' in s:
            iwać_suffixes.append(s.replace('yw', 'iw'))
        else:
            # uj- forms are identical for -iwać and -ywać
            iwać_suffixes.append(s)
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
    # Anterior adverbial participle
    ać_suffixes.append('awszy')
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
        # Verbal noun (hard-stem: rob+ienie)
        'ienie', 'ienia', 'ieniu', 'ieniem',
        'ieniach', 'ieniami', 'ieniom', 'ień',
        # Verbal noun (soft-stem: przybiel+enie, biel+enie)
        'enie', 'enia', 'eniu', 'eniem',
        'eniach', 'eniami', 'eniom', 'eń',
        # Verbal noun (-icie form, bić class: przybić→przybicie)
        'icie', 'icia', 'iciu', 'iciem',
        'iciach', 'iciami', 'iciom',
    ]
    # Anterior adverbial participle
    ić_suffixes.append('iwszy')
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
    # Anterior adverbial participle (imiesłów przysłówkowy uprzedni)
    yć_suffixes.append('ywszy')
    # być/przybyć future forms: przybędę, przybędzie etc. → przybyć
    yć_suffixes.extend([
        'ędę', 'ędziesz', 'ędzie', 'ędziemy', 'ędziecie', 'ędą',
    ])
    # Present tense type-2 (no -j-): przybliżyć→przybliżysz, przybliżymy
    # (przybliżycie already covered by verbal noun 'ycie' entry above)
    yć_suffixes.extend(['ysz', 'ymy'])
    # Passive participle (-ony form, shared with -ić but mapping to -yć)
    # e.g., przybliżony, zbliżony → przybliżyć, zbliżyć
    yć_suffixes.extend([
        'ony', 'ona', 'one',
        'onego', 'onej', 'onemu',
        'onym', 'onych', 'onymi', 'oną',
        'eni',
    ])
    # Verbal noun (-enie form, soft-stem -yć verbs): przybliżenie → przybliżyć
    yć_suffixes.extend([
        'enie', 'enia', 'eniu', 'eniem',
        'eniach', 'eniami', 'eniom', 'eń',
    ])
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
    # Present tense type-2 (bieżeć class): bieżysz, bieżymy, bieżycie → bieżeć
    eć_suffixes.extend(['ysz', 'ymy', 'ycie'])
    # Impersonal past (bieżeć class): przybieżano → przybieżeć
    eć_suffixes.append('ano')
    # Anterior adverbial participle
    eć_suffixes.extend(['ewszy', 'awszy'])
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
        # Virile plural past of -nieć type verbs (ładnieć→ładniali, przyblednieć→przybledniali)
        'iali', 'ialiśmy', 'ialiście',
        'ialiby', 'ialibyśmy', 'ialibyście',
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
    # Anterior adverbial participle
    ieć_suffixes.append('iewszy')
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
    # Anterior adverbial participle
    nąć_suffixes.append('nąwszy')
    for s in nąć_suffixes:
        maps.append((s, 'nąć'))

    # ===================== -nąć verbs (n-dropping past) =====================
    # Some -nąć verbs drop the -n- in past tense: zbladnąć→zbladł, przyblaknąć→przyblakł
    # Past forms come from bare stem (without the -n-).
    # Safety: mappings only trigger if stem+nąć exists in the dictionary.
    n_drop_past = [
        # Conditional
        'libyśmy', 'libyście', 'liby',
        'łybyśmy', 'łybyście', 'łyby',
        'łabym', 'łabyś', 'łaby',
        'łbym', 'łbyś', 'łby',
        'łoby',
        # Past virile plural
        'liśmy', 'liście',
        # Past non-virile plural
        'łyśmy', 'łyście', 'ły',
        # Past masc with personal endings
        'łem', 'łeś',
        # Past fem
        'łam', 'łaś', 'ła',
        # Past neut
        'ło',
        # Virile plural
        'li',
        # Anterior adverbial participle
        'łszy',
        # Masc sg past (bare ł — shortest, most ambiguous, try last)
        'ł',
    ]
    for s in n_drop_past:
        maps.append((s, 'nąć'))

    # ===================== -rać verbs (brać class) =====================
    # e.g., brać, zabrać, przybrać, nabrać, pobrać, wybrać, obrać
    # Present/future uses bior-/bierz- stems: biorę, bierzesz, bierze, ...
    # Imperative: bierz, bierzmy, bierzcie
    rać_bior_suffixes = [
        # Present/future 2sg, 3sg, 1pl, 2pl
        'ierzesz', 'ierze', 'ierzemy', 'ierzecie',
        # Imperative 2sg, 1pl, 2pl + particles
        'ierzmyż', 'ierzcież', 'ierzmy', 'ierzcie', 'ierzże', 'ierz',
        # 1sg and 3pl (stem: bior-)
        'iorę', 'iorą',
    ]
    for s in rać_bior_suffixes:
        maps.append((s, 'rać'))

    # ===================== -bić verbs (bić class) =====================
    # e.g., bić, przybić, dobić, wbić, ubić, zabić, zbić, pobić
    # Present/future uses bij- stem: biję, bijesz, bije, bijemy, bijecie, biją
    bić_present = [
        'ijesz', 'ijemy', 'ijecie', 'iją', 'ije', 'iję',
    ]
    for s in bić_present:
        maps.append((s, 'ić'))
    # Passive participle virile plural of bić-class (przybić → przybici)
    maps.append(('ici', 'ić'))

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
    # Anterior adverbial participle
    ąć_suffixes.append('ąwszy')
    for s in ąć_suffixes:
        maps.append((s, 'ąć'))

    # ===================== -iec verbs (g-alternation past) =====================
    # e.g., przybiec→przybiegł, biec→biegł (stem: przybi/bi + ec = przybiec/biec)
    iec_g_suffixes = [
        'iegł', 'iegła', 'iegłam', 'iegłaś', 'iegłeś', 'iegłem', 'iegło',
        'iegli', 'iegliśmy', 'iegliście',
        'iegliby', 'ieglibyśmy', 'ieglibyście',
        'iegłby', 'iegłbym', 'iegłbyś',
        'iegłaby', 'iegłabym', 'iegłabyś',
        'iegłoby', 'iegłszy',
        'iegłyby', 'iegłybyśmy', 'iegłybyście', 'iegłyśmy', 'iegłyście',
    ]
    for s in iec_g_suffixes:
        maps.append((s, 'iec'))

    # ===================== Imperative particle suffixes =====================
    # Polish imperatives: 2sg base + my (1pl) / cie (2pl) / że (emph) / myż / cież
    # These map the particle form back to its base imperative/verb form.
    # Only applied when the reconstructed base exists in the word set.
    imperative_particles = [
        # -dź imperative base (być, iść family: bądź, idź, przybądź)
        ('dźcież', 'dź'), ('dźmyż', 'dź'), ('dźcie', 'dź'), ('dźmy', 'dź'), ('dźże', 'dź'),
        # -ź imperative base
        ('źcież', 'ź'), ('źmyż', 'ź'), ('źcie', 'ź'), ('źmy', 'ź'), ('źże', 'ź'),
        # -w imperative base (-ić/-yć/-eć verbs with w-stem: barwić→barw, etc.)
        ('wcież', 'w'), ('wmyż', 'w'), ('wcie', 'w'), ('wmy', 'w'), ('wże', 'w'),
        # -j imperative base (-ać/-ować/-yć: daj, stój, etc.)
        ('jcież', 'j'), ('jmyż', 'j'), ('jcie', 'j'), ('jmy', 'j'), ('jże', 'j'),
        # -sz imperative base (pisać→pisz, nieść→nieś, etc.)
        ('szcież', 'sz'), ('szmyż', 'sz'), ('szcie', 'sz'), ('szmy', 'sz'), ('szże', 'sz'),
        # -ś imperative base
        ('ścież', 'ś'), ('śmyż', 'ś'), ('ście', 'ś'), ('śmy', 'ś'), ('śże', 'ś'),
    ]
    for conj_s, inf_s in imperative_particles:
        maps.append((conj_s, inf_s))

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

    # Genitive plural of -nięcie verbal nouns (from -nąć verbs)
    # e.g., przybiegnięć → przybiegnięcie
    maps.append(('nięć', 'nięcie'))

    # -ość nouns (e.g., radość, miłość)
    maps.append(('ością', 'ość'))
    maps.append(('ości', 'ość'))
    maps.append(('ościom', 'ość'))
    maps.append(('ościami', 'ość'))
    maps.append(('ościach', 'ość'))

    # ===== Fleeting 'e' (e ruchome) patterns =====

    # -ek nouns (e.g., przybytek → przybytk-, domek → domk-, kwiatek → kwiatk-)
    for case_suffix in ['kach', 'kami', 'ki', 'kom', 'kowi', 'ków', 'ku', 'kiem']:
        maps.append((case_suffix, 'ek'))

    # -ec nouns (e.g., chłopiec → chłopc-, kupiec → kupc-)
    for case_suffix in ['cach', 'cami', 'com', 'cowi', 'ców', 'cem', 'ca', 'cu', 'ce', 'cy']:
        maps.append((case_suffix, 'ec'))

    # -eń nouns (e.g., kamień → kamieni-, dzień → dni-/dniu-)
    for case_suffix in ['niach', 'niami', 'niom', 'niowi', 'niem', 'nia', 'niu', 'ni', 'niów']:
        maps.append((case_suffix, 'eń'))

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

    # -u (locative/vocative sg): przybyszu → przybysz, domu → dom
    maps.append(('u', ''))    # masc: przybyszu → przybysz
    maps.append(('u', 'o'))   # neut -o: mleku → mleko
    maps.append(('u', 'e'))   # neut -e: polu → pole

    # Palatalization k→c in -ka nouns (dat/loc sg): przybyszce → przybyszka
    maps.append(('ce', 'ka'))
    # Palatalization g→dz in -ga nouns (dat/loc sg): nodze → noga
    maps.append(('dze', 'ga'))

    # ===== Additional patterns to catch missed non-base forms =====

    # Gen sg of -ój nouns (przyboi → przybój)
    maps.append(('oi', 'ój'))
    # Nom/acc pl of -ój nouns (przyboje → przybój)
    maps.append(('oje', 'ój'))

    # Loc sg of -ąd/-ęd nouns with d→dź softening (przybłędzie → przybłęd)
    maps.append(('dzie', 'd'))

    # Dat/loc sg of -owa nouns (przybudowie → przybudowa)
    maps.append(('wie', 'wa'))

    # Gen pl of -ówka nouns (przybudówek → przybudówka)
    maps.append(('ówek', 'ówka'))

    # Nom pl of -rz/-sz nouns (przybierkarze → przybierkarz, marynarze → marynarz)
    maps.append(('e', ''))

    # Instr sg of neuter -e nouns (przybruczem → przybrucze)
    maps.append(('em', 'e'))

    # Loc sg of -r/-ór masculine nouns (przyborze → przybór via ó fix, kolorze → kolor)
    maps.append(('rze', 'r'))

    # Nom pl of -k/-g nouns (przybijaki → przybijak, banki → bank)
    maps.append(('i', ''))

    # Gen sg of -cie nouns (przyburcia → przyburcie)
    maps.append(('cia', 'cie'))
    # Gen pl of -cie nouns (przyburci → przyburcie)
    maps.append(('ci', 'cie'))

    # Gen pl of -owa nouns (przybudów → przybudowa)
    # Note: 'ów' → '' is tried first and handles -ów→'' cases; this handles -ów→'owa'
    maps.append(('ów', 'owa'))

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

        # Handle -nięć gen.pl (verbal noun of -nąć verbs) BEFORE the infinitive skip
        # e.g., przybiegnięć → przybiegnięcie
        if word.endswith('nięć') and len(word) > 4:
            stem = word[:-len('nięć')]
            if stem and (stem + 'nięcie') in word_set:
                to_remove.add(word)
                continue

        # Skip infinitives (they are base forms for verbs)
        if word.endswith('ć'):
            continue

        found = False

        # --- być/przybyć class: ądź imperative → yć infinitive (przybądź → przybyć) ---
        if word.endswith('ądź') and len(word) > 3:
            stem = word[:-3]
            infinitive = stem + 'yć'
            if infinitive in word_set and infinitive != word:
                to_remove.add(word)
                found = True
        if found:
            continue

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

        # --- 3rd person singular present of -ać verbs (e.g., przybywa → przybywać) ---
        # These end in 'a' which is too short for the general suffix map.
        # Verify by checking that 1st person 'am' or 3rd pl 'ają' also exist.
        if word.endswith('a') and len(word) > 4:
            stem = word[:-1]  # e.g., 'przybyw' from 'przybywa'
            infinitive = stem + 'ać'
            if infinitive in word_set and infinitive != word:
                if (stem + 'am') in word_set or (stem + 'ają') in word_set:
                    to_remove.add(word)
                    found = True
        if found:
            continue

        # --- Hard-stem -ić verb: 3sg present (i) and bare imperative ---
        # For -ić verbs with consonant stem (e.g., przybarwić, stem=przybarw):
        # 3sg: przybarwi; bare 2sg imperative: przybarw
        # Verify via: stem+isz or stem+ią (other present forms that are longer/safer)
        if not found:
            VOWELS = set('aeiouąęó')
            # 3sg present: word ends in 'i', stem is word[:-1]
            if word.endswith('i') and len(word) > 3:
                stem = word[:-1]
                if stem and stem[-1] not in VOWELS:
                    infinitive = stem + 'ić'
                    if infinitive in word_set and infinitive != word:
                        if (stem + 'isz') in word_set or (stem + 'ią') in word_set:
                            to_remove.add(word)
                            found = True
            # Bare imperative: word itself is stem, word+'ić'/'yć'/'eć' is infinitive
            if not found and len(word) > 3 and word[-1] not in VOWELS:
                for inf_end, present_end in (('ić', 'isz'), ('yć', 'ysz'), ('eć', 'ysz')):
                    infinitive = word + inf_end
                    if infinitive in word_set:
                        if (word + present_end) in word_set or (word + 'ą') in word_set:
                            to_remove.add(word)
                            found = True
                            break
            # Bare imperative + particles (my/cie/że/myż/cież) for -ić/-yć/-eć verbs
            # e.g., przybielmy, przybielcie, przybliżmy, przybieżcie
            if not found:
                for particle in ('cież', 'myż', 'cie', 'my', 'że'):
                    if word.endswith(particle):
                        stem = word[:-len(particle)]
                        if len(stem) > 2 and stem[-1] not in VOWELS:
                            for inf_end, present_end in (('ić', 'isz'), ('yć', 'ysz'), ('eć', 'ysz')):
                                infinitive = stem + inf_end
                                if infinitive in word_set:
                                    if (stem + present_end) in word_set or (stem + 'ą') in word_set:
                                        to_remove.add(word)
                                        found = True
                                        break
                        if found:
                            break
            # Imperative dz→dź softening (przybrudzić → przybrudź): suffix 'ź' → 'zić'
            # Verify via present form to avoid removing nouns like "miedź" (copper)
            if not found and word.endswith('ź') and len(word) > 3:
                stem = word[:-1]
                infinitive = stem + 'zić'
                if infinitive in word_set:
                    if (stem + 'zę') in word_set or (stem + 'zisz') in word_set or (stem + 'zą') in word_set:
                        to_remove.add(word)
                        found = True

        # --- -eć verb 3pl present (przybieżą → przybieżeć) ---
        # Verify via present 2sg form (przybieżysz) to confirm -eć class
        if not found and word.endswith('ą') and len(word) > 4:
            stem = word[:-1]
            for inf_end in ('eć', 'ieć'):
                infinitive = stem + inf_end
                if infinitive in word_set and infinitive != word:
                    if (stem + 'ysz') in word_set or (stem + 'ymy') in word_set:
                        to_remove.add(word)
                        found = True
                        break
        if found:
            continue

        # --- -eć verb 1sg present (przybieżę → przybieżeć) ---
        if not found and word.endswith('ę') and len(word) > 4:
            stem = word[:-1]
            for inf_end in ('eć', 'ieć'):
                infinitive = stem + inf_end
                if infinitive in word_set and infinitive != word:
                    if (stem + 'ysz') in word_set or (stem + 'ymy') in word_set:
                        to_remove.add(word)
                        found = True
                        break
        if found:
            continue

        # --- Adjective virile pl d→dz alternation (przybladzi → przyblady) ---
        if not found and word.endswith('dzi') and len(word) > 4:
            stem = word[:-3]
            base = stem + 'dy'
            if base in word_set and base != word:
                if (stem + 'dego') in word_set or (stem + 'dej') in word_set or (stem + 'dą') in word_set:
                    to_remove.add(word)
                    found = True
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
                # For 'e' → '' (nom pl of -rz/-sz nouns), protect neuter base forms ending in -e
                # and avoid removing base forms that happen to equal stem
                if suffix == 'e' and base_suffix == '':
                    # Only apply if stem ends in a consonant cluster typical for -rz/-sz nouns
                    if not stem or stem[-1] in set('aeiouąęóy'):
                        continue
                # For 'i' → '' (nom pl of -k/-g nouns), protect against virile adj pl
                # and only apply if stem itself is the base form in the word_set
                if suffix == 'i' and base_suffix == '':
                    # Skip if stem ends in a vowel (those are handled elsewhere)
                    if not stem or stem[-1] in set('aeiouąęóy'):
                        continue
                base = stem + base_suffix
                if base in word_set and base != word:
                    to_remove.add(word)
                    found = True
                    break
                # ó/o alternation fallback: try replacing last 'o' in stem with 'ó'
                # Handles: przyborem→przybór, przyborach→przybór, dworze→dwór, etc.
                if 'o' in stem:
                    last_o = stem.rfind('o')
                    alt_stem = stem[:last_o] + 'ó' + stem[last_o + 1:]
                    alt_base = alt_stem + base_suffix
                    if alt_base in word_set and alt_base != word:
                        to_remove.add(word)
                        found = True
                        break
        if found:
            continue

        # --- Masculine noun gen sg: 'a' ending with dative verification ---
        # e.g., przybijaka → przybijak (stem+'owi' exists as dative sg)
        if not found and word.endswith('a') and len(word) > 4:
            stem = word[:-1]
            if len(stem) >= 3 and stem not in {'', word}:
                if stem in word_set and stem != word:
                    if (stem + 'owi') in word_set or (stem + 'iem') in word_set:
                        to_remove.add(word)
                        found = True

        # --- Neuter noun gen sg: 'a' → 'e' with triple verification ---
        # e.g., przybrucza → przybrucze (confirmed by -ach, -ami, -em forms)
        if not found and word.endswith('a') and len(word) > 4:
            stem = word[:-1]
            base = stem + 'e'
            if len(stem) >= 3 and base in word_set and base != word:
                if ((stem + 'ach') in word_set and (stem + 'ami') in word_set
                        and (stem + 'em') in word_set):
                    to_remove.add(word)
                    found = True

        # --- Feminine vocative sg: 'o' → 'a' with -ami/-ach verification ---
        # e.g., przybudowo → przybudowa (vocative of -owa nouns)
        # Exclude stems ending in 'k' to protect neuter -ko nouns (przybierko, szybko, etc.)
        if not found and word.endswith('o') and len(word) > 4:
            stem = word[:-1]
            if len(stem) >= 3 and stem[-1] != 'k':
                base = stem + 'a'
                if base in word_set and base != word:
                    # Require instrumental plural to confirm it's a feminine -a noun
                    if (stem + 'ami') in word_set and (stem + 'ach') in word_set:
                        # Avoid removing adjective adverbs: check no adj gen/dat forms exist
                        if (stem + 'ego') not in word_set and (stem + 'ej') not in word_set:
                            to_remove.add(word)
                            found = True

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
