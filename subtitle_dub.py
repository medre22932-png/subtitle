#!/usr/bin/env python3
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

TIME_PATTERN = re.compile(
    r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
)

ARABIC_PHRASE_RE = re.compile(
    r'([\u0600-\u06FF]+(?:\s+[\u0600-\u06FF]+){2,})(?=[^\u0600-\u06FF.!؟،]|$)'
)

SURAHS = [
    "Fatiha", "Bakara", "Baqarah", "Ali İmran", "Âl-i İmrân", "Nisa", "Maide", "Enam",
    "Araf", "Enfal", "Tevbe", "Yunus", "Hud", "Yusuf", "Rad", "İbrahim", "Hicr", "Nahl",
    "İsra", "Kehf", "Meryem", "Taha", "Enbiya", "Hac", "Muminun", "Müminun", "Nur",
    "Furkan", "Şuara", "Neml", "Kasas", "Ankebut", "Rum", "Lokman", "Secde", "Ahzab",
    "Sebe", "Fatır", "Yasin", "Saffat", "Sad", "Zümer", "Mümin", "Fussilet", "Şura",
    "Zuhruf", "Duhan", "Casiye", "Ahkaf", "Muhammed", "Fetih", "Hucurat", "Kaf",
    "Zariyat", "Tur", "Necm", "Kamer", "Rahman", "Vakıa", "Hadid", "Mücadele", "Haşr",
    "Mümtehine", "Saff", "Cuma", "Münafikun", "Tegabun", "Talak", "Tahrim", "Mülk",
    "Kalem", "Hakka", "Mearic", "Nuh", "Cin", "Müzzemmil", "Müddessir", "Kıyamet",
    "İnsan", "Mürselat", "Nebe", "Naziat", "Abese", "Tekvir", "İnfitar", "Mutaffifin",
    "İnşikak", "Buruc", "Tarık", "Ala", "Gaşiye", "Fecr", "Beled", "Şems", "Leyl",
    "Duha", "İnşirah", "Tin", "Alak", "Kadir", "Beyyine", "Zilzal", "Adiyat", "Karia",
    "Tekasür", "Asr", "Hümeze", "Fil", "Kureyş", "Maun", "Kevser", "Kafirun", "Nasr",
    "Tebbet", "İhlas", "Felak", "Nas"
]

SPLIT_PUNCTUATION = {".", "!", "?", ";", ":", ","}
STRONG_PUNCTUATION = {".", "!", "?", ";"}


def srt_time_to_ms(h, m, s, ms):
    return (((int(h) * 60 + int(m)) * 60 + int(s)) * 1000) + int(ms)


def ms_to_srt_time(total_ms):
    total_ms = max(0, int(round(total_ms)))
    h = total_ms // 3600000
    total_ms %= 3600000
    m = total_ms // 60000
    total_ms %= 60000
    s = total_ms // 1000
    ms = total_ms % 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def parse_timecode(line):
    match = TIME_PATTERN.search(line)
    if not match:
        return None
    start_ms = srt_time_to_ms(match.group(1), match.group(2), match.group(3), match.group(4))
    end_ms = srt_time_to_ms(match.group(5), match.group(6), match.group(7), match.group(8))
    return start_ms, end_ms


def clean_brackets_and_citations(text, remove_brackets=True):
    """
    Cleans tags and citations. If remove_brackets is True, it strips [ ] tags.
    """
    if remove_brackets:
        text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[\'"]?\+\d+[\'"]?', '', text)
    return text


def replace_surah_parens(text):
    def repl(match):
        inner = match.group(1)
        
        # Check for numerical Surah:Ayah formats (e.g., 55:7)
        if re.fullmatch(r'\d+\s*:\s*\d+', inner.strip()):
            return f"[{inner}]"
            
        # Original: Check for Surah names
        for s in SURAHS:
            if s in inner:
                return f"[{inner}]"
                
        return match.group(0)

    return re.sub(r'\(([^)]+)\)', repl, text)


def expand_honorifics(text):
    """For dubbing TXT output: expand only clearly-marked honorifics."""
    replacements = [
        (r'\(\s*s\.?\s*a\.?\s*v\.?\s*\)', '(sallallahu aleyhi ve sellem)'),
        (r'\(\s*s\.?\s*a\.?\s*w\.?\s*\)', '(sallallahu aleyhi ve sellem)'),
        (r'\(\s*a\.?\s*s\.?\s*\)', '(aleyhisselam)'),
        (r'\(\s*r\.?\s*a\.?\s*nha\.?\s*\)', '(radıyallahu anha)'),
        (r'\(\s*r\.?\s*a\.?\s*nhu\.?\s*\)', '(radıyallahu anhu)'),
        (r'\(\s*r\.?\s*a\.?\s*\)', '(radıyallahu anh)'),
        (r'\(\s*r\.?\s*h\.?\s*\)', '(rahmetullahi aleyh)'),
        (r'\(\s*c\.?\s*c\.?\s*\)', '(celle celaluhu)'),
        (r'\(\s*j\.?\s*j\.?\s*\)', '(celle celaluhu)'),

        (r'\bs\.\s*a\.\s*v\.?\b', 'sallallahu aleyhi ve sellem'),
        (r'\bs\.\s*a\.\s*w\.?\b', 'sallallahu aleyhi ve sellem'),
        (r'\ba\.\s*s\.?\b', 'aleyhisselam'),
        (r'\br\.\s*a\.\s*nha\.?\b', 'radıyallahu anha'),
        (r'\br\.\s*a\.\s*nhu\.?\b', 'radıyallahu anhu'),
        (r'\br\.\s*a\.?\b', 'radıyallahu anh'),
        (r'\br\.\s*h\.?\b', 'rahmetullahi aleyh'),
        (r'\bc\.\s*c\.?\b', 'celle celaluhu'),
        (r'\bj\.\s*j\.?\b', 'celle celaluhu'),
    ]

    for pattern, expansion in replacements:
        text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)

    return text


def compress_honorifics_for_srt(text):
    """For subtitle SRT output: compress full honorifics into standard abbreviations."""
    replacements = [
        (r'\(\s*aleyhisselam\s*\)', '(a.s)'),
        (r'\baleyhisselam\b', '(a.s)'),

        (r'\(\s*sallallahu aleyhi ve sellem\s*\)', '(s.a.v)'),
        (r'\bsallallahu aleyhi ve sellem\b', '(s.a.v)'),

        (r'\(\s*radıyallahu anha\s*\)', '(r.a)'),
        (r'\bradıyallahu anha\b', '(r.a)'),

        (r'\(\s*radıyallahu anhu\s*\)', '(r.a)'),
        (r'\bradıyallahu anhu\b', '(r.a)'),

        (r'\(\s*radıyallahu anh\s*\)', '(r.a)'),
        (r'\bradıyallahu anh\b', '(r.a)'),

        (r'\(\s*rahmetullahi aleyh\s*\)', '(r.h)'),
        (r'\brahmetullahi aleyh\b', '(r.h)'),

        (r'\(\s*celle celaluhu\s*\)', '(ﷻ)'),
        (r'\bcelle celaluhu\b', '(ﷻ)'),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # normalize duplicate parentheses like "((a.s))"
    text = re.sub(r'\(\s*\(([^()]+)\)\s*\)', r'(\1)', text)

    # normalize accidental spaces before suffix apostrophe: "(a.s) 'a" -> "(a.s)'a"
    text = re.sub(r'(\([^)]+\))\s+\'', r"\1'", text)

    # collapse spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def shift_apostrophe_suffixes(text):
    h_list = [
        'sallallahu aleyhi ve sellem', 'aleyhisselam',
        'radıyallahu anha', 'radıyallahu anhu', 'radıyallahu anh', 'radiyallahu anhum',
        'rahmetullahi aleyh', 'celle celaluhu', 'azze ve celle'
    ]

    honorific_endings = {
        'sallallahu aleyhi ve sellem': {'gen': 'in', 'dat': 'e', 'acc': 'i', 'loc': 'de', 'abl': 'den', 'ins': 'le'},
        'aleyhisselam': {'gen': 'ın', 'dat': 'a', 'acc': 'ı', 'loc': 'da', 'abl': 'dan', 'ins': 'la'},
        'radıyallahu anha': {'gen': 'nın', 'dat': 'ya', 'acc': 'yı', 'loc': 'da', 'abl': 'dan', 'ins': 'yla'},
        'radıyallahu anhu': {'gen': 'nun', 'dat': 'ya', 'acc': 'yu', 'loc': 'da', 'abl': 'dan', 'ins': 'yla'},
        'radıyallahu anh': {'gen': 'ın', 'dat': 'a', 'acc': 'ı', 'loc': 'da', 'abl': 'dan', 'ins': 'la'},
        'radiyallahu anhum': {'gen': 'un', 'dat': 'a', 'acc': 'u', 'loc': 'da', 'abl': 'dan', 'ins': 'la'},
        'rahmetullahi aleyh': {'gen': 'in', 'dat': 'e', 'acc': 'i', 'loc': 'de', 'abl': 'den', 'ins': 'le'},
        'celle celaluhu': {'gen': 'nun', 'dat': 'ya', 'acc': 'yu', 'loc': 'da', 'abl': 'dan', 'ins': 'yla'},
        'azze ve celle': {'gen': 'nin', 'dat': 'ye', 'acc': 'yi', 'loc': 'de', 'abl': 'den', 'ins': 'yle'}
    }

    def get_case(suf):
        suf = suf.lower()
        if suf in ['in', 'ın', 'un', 'ün', 'nin', 'nın', 'nun', 'nün']:
            return 'gen'
        if suf in ['e', 'a', 'ye', 'ya']:
            return 'dat'
        if suf in ['i', 'ı', 'u', 'ü', 'yi', 'yı', 'yu', 'yü']:
            return 'acc'
        if suf in ['de', 'da', 'te', 'ta']:
            return 'loc'
        if suf in ['den', 'dan', 'ten', 'tan']:
            return 'abl'
        if suf in ['le', 'la', 'yle', 'yla']:
            return 'ins'
        return None

    h_pattern = '|'.join(h_list)
    pattern = re.compile(
        r"(\b\w+)'([A-Za-zıİöÖüÜçÇşŞğĞ]+)(\s*\(?\s*)(" + h_pattern + r")(\s*\)?)",
        re.IGNORECASE
    )

    def repl(match):
        word = match.group(1)
        orig_suf = match.group(2)
        spacer = match.group(3)
        honorific = match.group(4)
        close_paren = match.group(5)

        case = get_case(orig_suf)
        h_key = honorific.lower()

        if case and h_key in honorific_endings:
            new_suf = honorific_endings[h_key][case]
            return f"{word}{spacer}{honorific}{close_paren}'{new_suf}"

        return match.group(0)

    return pattern.sub(repl, text)


def dot_arabic_phrases(text):
    return ARABIC_PHRASE_RE.sub(r'\1.', text)


def process_text_for_srt(text):
    text = clean_brackets_and_citations(text, remove_brackets=True)
    text = shift_apostrophe_suffixes(text)
    text = compress_honorifics_for_srt(text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def process_text_for_dubbing(text):
    text = clean_brackets_and_citations(text, remove_brackets=False)
    text = replace_surah_parens(text)
    text = expand_honorifics(text)
    text = shift_apostrophe_suffixes(text)
    text = dot_arabic_phrases(text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_srt_blocks(content):
    raw_blocks = [block.strip() for block in content.replace('\r\n', '\n').split('\n\n') if block.strip()]
    parsed = []

    for raw in raw_blocks:
        lines = raw.split('\n')
        if len(lines) < 2:
            continue

        idx = None
        time_line = None
        text_lines = []

        if re.fullmatch(r'\d+', lines[0].strip()) and len(lines) >= 2:
            idx = int(lines[0].strip())
            time_line = lines[1].strip()
            text_lines = lines[2:]
        else:
            time_line = lines[0].strip()
            text_lines = lines[1:]

        parsed_time = parse_timecode(time_line)
        if not parsed_time:
            continue

        start_ms, end_ms = parsed_time
        text = ' '.join(line.strip() for line in text_lines if line.strip())

        parsed.append({
            'index': idx,
            'start_ms': start_ms,
            'end_ms': end_ms,
            'text': text
        })

    return parsed


def tokenize_with_boundaries(text):
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r'\S+', text)]


def token_has_split_punctuation(token):
    stripped = token.rstrip('\'"”’)]}')
    return any(ch in stripped for ch in SPLIT_PUNCTUATION)


def token_has_strong_punctuation(token):
    stripped = token.rstrip('\'"”’)]}')
    return any(ch in stripped for ch in STRONG_PUNCTUATION)


def choose_split_index(tokens, start_idx=0, trigger_length=18, target=12, max_valid=20, hard_limit=42):
    remaining = len(tokens) - start_idx
    
    # If the text is 18 words or shorter, don't split
    if remaining <= trigger_length:
        return None

    # Helper function to find word positions (relative to current chunk) that contain punctuation
    def get_puncts(check_func):
        puncts = []
        for loc in range(1, remaining + 1):
            idx = start_idx + loc - 1
            if check_func(tokens[idx][0]):
                puncts.append(loc)  # loc is the length of the left part if we split here
        return puncts

    strong_puncts = get_puncts(token_has_strong_punctuation)
    weak_puncts = get_puncts(token_has_split_punctuation) # Note: this includes strong punctuation too

    # 1. Closest STRONG punctuation to the 12th word
    if strong_puncts:
        closest_strong = min(strong_puncts, key=lambda x: abs(x - target))
        # Ensure neither the left part nor the remaining right part exceeds 20 words
        if closest_strong <= max_valid and (remaining - closest_strong) <= max_valid:
            return start_idx + closest_strong

    # 2. Fallback: First STRONG punctuation after 12 until 20
    strong_13_to_20 = [x for x in strong_puncts if target < x <= max_valid]
    if strong_13_to_20:
        return start_idx + strong_13_to_20[0]

    # 3. Closest WEAK punctuation to the 12th word
    if weak_puncts:
        closest_weak = min(weak_puncts, key=lambda x: abs(x - target))
        # Ensure neither the left part nor the remaining right part exceeds 20 words
        if closest_weak <= max_valid and (remaining - closest_weak) <= max_valid:
            return start_idx + closest_weak

    # 4. Fallback: First WEAK punctuation after 12 until 20
    weak_13_to_20 = [x for x in weak_puncts if target < x <= max_valid]
    if weak_13_to_20:
        return start_idx + weak_13_to_20[0]

    # 5. Fallback: First WEAK or STRONG punctuation after 20 until 42
    # (weak_puncts naturally contains strong punctuation as well)
    any_21_to_42 = [x for x in weak_puncts if max_valid < x <= hard_limit]
    if any_21_to_42:
        return start_idx + any_21_to_42[0]

    # 6. Hard Limit: If absolutely no punctuation exists, split at the limit (42) or the end
    return start_idx + min(remaining, hard_limit)


def split_text_robust(text, trigger_length=18, target=12, max_valid=20, hard_limit=42):
    tokens = tokenize_with_boundaries(text)
    
    if len(tokens) <= trigger_length:
        return [text.strip()]

    parts = []
    start_idx = 0

    while start_idx < len(tokens):
        split_idx = choose_split_index(tokens, start_idx, trigger_length, target, max_valid, hard_limit)
        
        if split_idx is None:
            part = ' '.join(tok for tok, _, _ in tokens[start_idx:]).strip()
            if part:
                parts.append(part)
            break

        part = ' '.join(tok for tok, _, _ in tokens[start_idx:split_idx]).strip()
        if part:
            parts.append(part)
        start_idx = split_idx

    # Merge orphans (less than 4 words) into the previous chunk
    if len(parts) >= 2 and len(parts[-1].split()) < 4:
        parts[-2] = f"{parts[-2]} {parts[-1]}".strip()
        parts.pop()

    return parts


def split_timestamps_proportionally(start_ms, end_ms, text_parts):
    if len(text_parts) == 1:
        return [(start_ms, end_ms)]

    total_duration = max(1, end_ms - start_ms)
    lengths = [max(1, len(part)) for part in text_parts]
    total_len = sum(lengths)

    boundaries = [start_ms]
    elapsed = 0

    for i in range(len(text_parts) - 1):
        elapsed += lengths[i]
        boundary = start_ms + round(total_duration * (elapsed / total_len))
        boundaries.append(boundary)

    boundaries.append(end_ms)

    ranges = []
    for i in range(len(text_parts)):
        part_start = boundaries[i]
        part_end = boundaries[i + 1]
        if part_end < part_start:
            part_end = part_start
        ranges.append((part_start, part_end))

    return ranges


def extend_timestamps_to_next(blocks):
    """
    Extends the end timestamp of each block to match the start timestamp of the next block.
    """
    for i in range(len(blocks) - 1):
        if blocks[i]['end_ms'] < blocks[i+1]['start_ms']:
            blocks[i]['end_ms'] = blocks[i+1]['start_ms']
    return blocks


def build_output_srt(blocks):
    intermediate_blocks = []

    # First, collect all the cleaned and proportionally split blocks into an intermediate list
    for block in blocks:
        cleaned = process_text_for_srt(block['text'])
        if not cleaned:
            continue

        parts = split_text_robust(cleaned, trigger_length=18, target=12, max_valid=20, hard_limit=42)
        time_ranges = split_timestamps_proportionally(block['start_ms'], block['end_ms'], parts)

        for part_text, (part_start, part_end) in zip(parts, time_ranges):
            intermediate_blocks.append({
                'start_ms': part_start,
                'end_ms': part_end,
                'text': part_text
            })

    # Apply the extension rule to snap timestamps together
    intermediate_blocks = extend_timestamps_to_next(intermediate_blocks)

    # Finally, format them into standard SRT text blocks
    output_blocks = []
    counter = 1
    for block in intermediate_blocks:
        output_blocks.append(
            f"{counter}\n"
            f"{ms_to_srt_time(block['start_ms'])} --> {ms_to_srt_time(block['end_ms'])}\n"
            f"{block['text']}"
        )
        counter += 1

    return output_blocks


def merge_close_blocks_to_paragraphs(blocks, max_gap_ms=299):
    if not blocks:
        return []

    processed = []
    for block in blocks:
        cleaned = process_text_for_dubbing(block['text'])
        if cleaned:
            processed.append({
                'start_ms': block['start_ms'],
                'end_ms': block['end_ms'],
                'text': cleaned
            })

    if not processed:
        return []

    merged = []
    current = processed[0].copy()

    for block in processed[1:]:
        gap = block['start_ms'] - current['end_ms']

        if gap <= max_gap_ms:
            current['end_ms'] = max(current['end_ms'], block['end_ms'])
            current['text'] = (current['text'] + ' ' + block['text']).strip()
        else:
            merged.append(current)  
            current = block.copy()

    merged.append(current)
    return merged


def select_file_and_process():
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo("Step 1", "Select the SRT file to clean")
    srt_path = filedialog.askopenfilename(
        title="Select SRT File",
        filetypes=[("SRT files", "*.srt")]
    )
    if not srt_path:
        return

    file_dir = os.path.dirname(srt_path)
    file_name = os.path.splitext(os.path.basename(srt_path))[0]

    output_srt_path = os.path.join(file_dir, f"{file_name} subtitle.srt")
    output_dubbing_srt_path = os.path.join(file_dir, f"{file_name} dubbing.srt")

    try:
        with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        blocks = parse_srt_blocks(content)

        if not blocks:
            messagebox.showerror("Error", "No valid subtitle blocks were found in the selected SRT.")
            return

        # 1. Standard Subtitle SRT Output
        srt_blocks = build_output_srt(blocks)

        # Get merged blocks (contains text + timestamps)
        merged_dubbing_blocks = merge_close_blocks_to_paragraphs(blocks, max_gap_ms=299)

        # 2. Dubbing Output formatted as standard SRT
        dubbing_srt_blocks = []
        for i, block in enumerate(merged_dubbing_blocks, start=1):
            start_str = ms_to_srt_time(block['start_ms'])
            end_str = ms_to_srt_time(block['end_ms'])
            dubbing_srt_blocks.append(f"{i}\n{start_str} --> {end_str}\n{block['text']}")

        # Write files
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(srt_blocks) + '\n')

        with open(output_dubbing_srt_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(dubbing_srt_blocks) + '\n')

        messagebox.showinfo(
            "Success",
            "Done!\n\n"
            f"Created Subtitle SRT:\n{os.path.basename(output_srt_path)}\n\n"
            f"Created Dubbing SRT:\n{os.path.basename(output_dubbing_srt_path)}"
        )

    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    select_file_and_process()
