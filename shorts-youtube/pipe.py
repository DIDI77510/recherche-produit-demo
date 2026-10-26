# Pipeline Shorts "Renaissance Amoureuse" (workbench Composio)
import os, json, subprocess, re, sys, requests
BASE = '/home/user/shorts'
VOICE = '7hvlKIUQMQekYdn00slv'          # voix "Couple" (ElevenLabs de BIB)
EL_ACCOUNT = 'elevenlabs_mash-orgeat'
CHANNEL = 'UCDEVWt4Cv_HUtdixoNDr9PA'
BOOK = 'https://www.amazon.fr/dp/B0HP5KYMJZ'
CTA_SAY = "Et si vous voulez trente exercices comme celui-ci, mon guide « 30 jours pour reconnecter son couple » est en lien dans la description."
CTA_SHOW = "30 exercices comme celui-ci ?\\N➜ mon guide en lien dans la description"
GAP, LEAD, TAIL = 0.28, 0.15, 0.7

def ffmpeg():
    try:
        import imageio_ffmpeg
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'imageio-ffmpeg'], check=True)
        import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def setup():
    os.makedirs(BASE + '/fonts', exist_ok=True)
    fonts = {'Poppins-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf',
             'Poppins-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf',
             'Lora.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf'}
    for n, u in fonts.items():
        p = f'{BASE}/fonts/{n}'
        if not os.path.exists(p):
            r = requests.get(u, timeout=60); r.raise_for_status(); open(p, 'wb').write(r.content)
    return ffmpeg()

def dur(path):
    out = subprocess.run([ffmpeg(), '-i', path], capture_output=True, text=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)

def specs():
    return json.load(open(BASE + '/specs.json'))

def tts(k, run_composio_tool):
    sp = specs()[str(k)]; d = f'{BASE}/{k}'; os.makedirs(d, exist_ok=True)
    says = sp['chunks'] + [CTA_SAY]
    for i, t in enumerate(says):
        p = f'{d}/a_{i:02d}.mp3'
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            continue
        r, e = run_composio_tool('ELEVENLABS_TEXT_TO_SPEECH', {'voice_id': VOICE, 'text': t, 'model_id': 'eleven_v4',
                                 'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}}, account=EL_ACCOUNT)
        if e:
            r, e = run_composio_tool('ELEVENLABS_TEXT_TO_SPEECH', {'voice_id': VOICE, 'text': t, 'model_id': 'eleven_multilingual_v2'}, account=EL_ACCOUNT)
        if e:
            raise RuntimeError(f'TTS {i}: {e}')
        f = (r.get('data') or {}).get('file') or {}
        u = f.get('s3url') or f.get('url')
        open(p, 'wb').write(requests.get(u, timeout=60).content)
    return len(says)

def clips(k):
    sp = specs()[str(k)]; d = f'{BASE}/{k}'
    for j, c in enumerate(sp['clips']):
        p = f'{d}/c_{j}.mp4'
        if not os.path.exists(p) or os.path.getsize(p) < 100000:
            r = requests.get('https://videos.pexels.com/video-files/' + c, timeout=120, headers={'User-Agent': 'Mozilla/5.0'})
            r.raise_for_status(); open(p, 'wb').write(r.content)
    return len(sp['clips'])

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def _bg(sh, d, name):
    open(f'{d}/{name}.sh','w').write(sh)
    subprocess.Popen(['nohup','bash',f'{d}/{name}.sh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

def prep(k):
    """Étape rapide : voix assemblée + sous-titres + lance la conversion des clips en 720p (arrière-plan)."""
    import shlex
    ff = ffmpeg(); sp = specs()[str(k)]; d = f'{BASE}/{k}'
    shows = sp['chunks'] + [CTA_SHOW]; n = len(shows)
    ad = [dur(f'{d}/a_{i:02d}.mp3') for i in range(n)]
    t = LEAD; ev = []
    for i in range(n):
        ev.append((t, t + ad[i] + 0.15, shows[i])); t += ad[i] + GAP
    T = round(t - GAP + TAIL, 2)
    inp = []; fc = []
    for i in range(n):
        inp += ['-i', f'{d}/a_{i:02d}.mp3']
        pad = GAP if i < n - 1 else TAIL
        delay = int(LEAD * 1000) if i == 0 else 0
        fc.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=mono,adelay={delay},apad=pad_dur={pad}[a{i}]')
    fc.append(''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1,loudnorm=I=-14:TP=-1.5[out]')
    subprocess.run([ff, '-y', '-v', 'error'] + inp + ['-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '44100', f'{d}/voice.m4a'], check=True)
    ass = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 1080', 'PlayResY: 1920', 'WrapStyle: 0', '', '[V4+ Styles]',
           'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
           'Style: Cap,Poppins,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,2,2,90,90,520,1',
           'Style: Hook,Lora,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,3,18,0,8,90,90,230,1',
           'Style: Brand,Poppins,40,&H00C8E0FF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,3,1,8,70,70,120,1', '',
           '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
           f"Dialogue: 1,{ts(0)},{ts(3.2)},Hook,,0,0,0,,{{\\fad(200,300)}}{sp['hook']}",
           f'Dialogue: 0,{ts(3.3)},{ts(T)},Brand,,0,0,0,,RENAISSANCE AMOUREUSE']
    for a, b, s in ev:
        ass.append(f'Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\fad(100,100)}}{s}')
    open(f'{d}/subs.ass', 'w').write('\n'.join(ass) + '\n')
    nc = len(sp['clips']); seg = T / nc
    json.dump({'T': T, 'seg': seg, 'nc': nc}, open(f'{d}/plan.json', 'w'))
    S = 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30,setsar=1,format=yuv420p'
    lines = []
    for j in range(nc):
        cd = dur(f'{d}/c_{j}.mp4'); off = max(0.0, min(1.0, cd - seg))
        vf = f'{S},tpad=stop_mode=clone:stop_duration={seg:.2f},trim=duration={seg:.3f},setpts=PTS-STARTPTS'
        cmd = [ff, '-y', '-v', 'error', '-ss', f'{off:.2f}', '-t', f'{seg + 0.1:.2f}', '-i', f'{d}/c_{j}.mp4', '-vf', vf, '-an',
               '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '20', f'{d}/p_{j}.mp4']
        lines.append(' '.join(shlex.quote(x) for x in cmd))
    for f in os.listdir(d):
        if f.endswith('.done'): os.remove(f'{d}/{f}')
    _bg(' && '.join(lines) + f' > {d}/clips.log 2>&1; touch {d}/clips.done', d, 'clips')
    return {'duration': T, 'clips_started': nc}

def final(k):
    """Assemble les clips 720p + sous-titres + voix (arrière-plan). Attendre final.done."""
    import shlex
    ff = ffmpeg(); d = f'{BASE}/{k}'; p = json.load(open(f'{d}/plan.json')); nc = p['nc']
    open(f'{d}/list.txt', 'w').write(''.join(f"file '{d}/p_{j}.mp4'\n" for j in range(nc)))
    out = f'{d}/short_{k}.mp4'
    cmd = [ff, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{d}/list.txt', '-i', f'{d}/voice.m4a',
           '-vf', f'ass={d}/subs.ass:fontsdir={BASE}/fonts', '-map', '0:v', '-map', '1:a', '-t', f"{p['T']}",
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-maxrate', '3000k', '-bufsize', '6000k',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out]
    sheet = [ff, '-y', '-v', 'error', '-i', out, '-vf', 'fps=1/3,scale=180:-1,tile=7x2', '-frames:v', '1', f'{d}/sheet.jpg']
    _bg(' '.join(shlex.quote(x) for x in cmd) + f' > {d}/final.log 2>&1 && ' + ' '.join(shlex.quote(x) for x in sheet) + f'; touch {d}/final.done', d, 'final')
    return {'final_started': True}

def status(k):
    d = f'{BASE}/{k}'
    r = {x: os.path.exists(f'{d}/{x}.done') for x in ('clips', 'final')}
    for x in ('clips', 'final'):
        if os.path.exists(f'{d}/{x}.log'):
            r[x + '_log'] = open(f'{d}/{x}.log').read()[-300:]
    o = f'{d}/short_{k}.mp4'
    r['size_mb'] = round(os.path.getsize(o) / 1e6, 2) if os.path.exists(o) else 0
    return r

def description(k):
    sp = specs()[str(k)]
    return (sp['lead'] + f"\n\n📖 30 exercices comme celui-ci, un par jour : le guide « 30 jours pour reconnecter son couple » sur Amazon Kindle → {BOOK}"
            "\n\nAbonnez-vous à Renaissance Amoureuse pour des conseils concrets chaque semaine."
            "\n\nSi vous subissez des violences dans votre couple, ce n'est pas un problème de communication : appelez le 3919 (gratuit et anonyme)."
            "\n\nVoix : ElevenLabs\nImages : Pexels\n\n#couple #conseilcouple #relationamoureuse")

TAGS = ['couple', 'conseil couple', 'relation amoureuse', 'communication couple', 'couple en crise', 'raviver la flamme']

def publish(k, run_composio_tool, upload_local_file, proxy_execute):
    sp = specs()[str(k)]; d = f'{BASE}/{k}'; out = f'{d}/short_{k}.mp4'
    up, e = upload_local_file(out)
    if e:
        return {'ok': False, 'step': 'upload_local_file', 'error': str(e)}
    up = up.get('data', up)
    s3key, s3url = up.get('s3key'), up.get('s3_url')
    desc = description(k)
    r, e = run_composio_tool('YOUTUBE_MULTIPART_UPLOAD_VIDEO', {'title': sp['title'], 'description': desc, 'categoryId': '22',
                             'privacyStatus': 'public', 'tags': TAGS,
                             'videoFile': {'name': f'short_{k}.mp4', 'mimetype': 'video/mp4', 's3key': s3key}})
    if e:
        return {'ok': False, 'step': 'youtube_upload', 'error': str(e)[:400], 'video_url_for_manual_upload': s3url,
                'title': sp['title'], 'description': desc}
    data = r.get('data', r)
    vid = data.get('id') or (data.get('response_data') or {}).get('id') or (data.get('data') or {}).get('id')
    res = {'ok': True, 'video_id': vid, 'url': f'https://youtube.com/shorts/{vid}'}
    body = {'id': vid, 'snippet': {'title': sp['title'], 'description': desc, 'categoryId': '22', 'tags': TAGS,
                                   'defaultLanguage': 'fr', 'defaultAudioLanguage': 'fr-FR'}}
    r2, e2 = proxy_execute('PUT', 'https://www.googleapis.com/youtube/v3/videos', 'youtube', query_params={'part': 'snippet'}, body=body)
    res['language_set'] = not e2
    if e2:
        res['language_error'] = str(e2)[:200]
    r3, e3 = proxy_execute('PUT', 'https://www.googleapis.com/youtube/v3/videos', 'youtube', query_params={'part': 'status'},
                           body={'id': vid, 'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}})
    res['kids_set'] = not e3
    json.dump({'last_published': k, 'video_id': vid}, open(f'{BASE}/state.json', 'w'))
    return res
