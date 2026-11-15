#!/usr/bin/env python3
"""Render a Turkish cinematic story video using free local tools."""
from pathlib import Path
import asyncio, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
WORK = OUT / "work"
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)
W, H = 1280, 720
SCENES = [
("03:17", "Saat 03:17'ydi. Mert, telefonunun titremesiyle uyandı. Ekranda kendi numarasından gönderilmiş tek bir mesaj vardı: Beş dakika sonra kapın çalacak. Sakın açma. Mert önce bunun kötü bir şaka olduğunu düşündü. Ama mesajın gönderildiği numara... kendi numarasıydı.", "PHONE"),
("TANIMADIĞI MESAJ", "Mesajın altında bir fotoğraf vardı. Kendi salonu. Kendi koltuğu. Fotoğraf birkaç saniye önce çekilmiş gibiydi. Mert yataktan kalktı, evin ışıklarını açtı. Ev bomboştu. Sonra telefon yeniden titredi: Işıkları kapat. Seni görmesin.", "PHOTO"),
("İLK VURUŞ", "Tam o anda kapı çaldı. Bir kez. Sonra iki kez daha. Mert nefesini tuttu. Kapının ardından bir ses duyuldu. Oğlum... aç kapıyı. Bu ses, yıllar önce kaybettiği babasının sesiydi. Mert'in eli kapı koluna uzandı ama mesajı hatırladı.", "DOOR"),
("BABASININ SESİ", "Kapının ardından ses yeniden geldi. Mert, üşüdüm oğlum. Sadece bir dakika. Mert'in gözleri doldu. Babasının ölümünden beri bu sesi bir kez daha duymak için her şeyi verebilirdi. Telefonuna baktı. Yeni mesaj: O ses baban değil. Sakın cevap verme.", "SHADOW"),
("FOTOĞRAF", "Bir fotoğraf daha geldi. Bu kez kapının önünde duran kişi görünüyordu. Üzerinde Mert'in kendi kıyafetleri vardı. Yüzü karanlıktaydı. Fotoğrafın arkasında tek cümle yazıyordu: İçeri alırsan, sabah sen burada olmayacaksın. Mert geri çekildi.", "WARNING"),
("AYNADAKİ", "Koridordaki aynadan bir tıkırtı geldi. Mert başını çevirdi. Aynadaki yansıması ona bakıyordu ama Mert kıpırdamıyordu. Yansıma yavaşça gülümsedi. Sonra dudakları hareket etti: Kapıyı aç. Mert donakaldı. Aynadaki kendisi, kapının önündeki sesten daha yakındı.", "MIRROR"),
("SON MESAJ", "Telefon ekranı kendi kendine açıldı. Gönderen yine Mert'in numarasıydı. Mesaj kısaydı: Artık beni dinleme. Ben gelecekteki senim. Kapıyı açarsan bu gece bitecek. Mert titreyen parmaklarıyla cevap yazdı: Peki ya açmazsam? Yanıt anında geldi: O zaman ben içeri giremem.", "PHONE2"),
("03:22", "Kapı kolu yavaşça aşağı indi. Mert geriye doğru sendeledi. Aynadaki yansıması artık arkasında duruyordu. Telefon son kez titredi. Ekranda tek satır belirdi: Bu sefer... kapıyı sen açma. Kapı kilidi döndü. Görüntü karardı. Bazı mesajlar geleceği haber vermez. Geleceği başlatır.", "END"),
]

def font(size, bold=False):
    candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def make_frame(index, title, caption, motif):
    im = Image.new("RGB", (W,H), (7,10,17))
    px = im.load()
    # restrained midnight-blue gradient and vignette
    for y in range(H):
        for x in range(W):
            glow = max(0, 1 - (((x-850)/700)**2 + ((y-330)/520)**2))
            v = int(9 + glow*15)
            px[x,y] = (v//2, v, v+10)
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((0,0,W,9), fill=(160,35,45,230))
    # cinematic silhouettes / scene symbols
    if motif in ("DOOR","SHADOW","END"):
        d.rectangle((830,95,1110,650), fill=(3,5,10,255), outline=(85,95,115,180), width=5)
        d.ellipse((1068,360,1088,380), fill=(190,155,95,220))
        if motif == "SHADOW":
            d.ellipse((900,205,1030,335), fill=(2,3,7,255))
            d.polygon([(875,620),(900,330),(1030,330),(1070,620)], fill=(2,3,7,255))
    elif motif in ("PHONE","PHONE2","PHOTO"):
        d.rounded_rectangle((900,130,1080,560), radius=28, fill=(2,4,8,255), outline=(120,135,155,230), width=5)
        d.rounded_rectangle((920,165,1060,510), radius=12, fill=(14,23,35,255))
        d.text((940,205),"03:17",font=font(38,True),fill=(230,235,245,255))
        d.rectangle((940,275,1040,282),fill=(160,35,45,255))
        d.text((940,310),"1 yeni mesaj",font=font(18),fill=(205,215,230,255))
    elif motif == "MIRROR":
        d.rounded_rectangle((850,90,1110,650), radius=110, fill=(2,4,8,255), outline=(110,125,145,210), width=6)
        d.ellipse((930,185,1030,285), fill=(18,24,34,255))
        d.polygon([(900,590),(925,300),(1040,300),(1070,590)], fill=(18,24,34,255))
    else:
        d.ellipse((900,170,1080,350), outline=(140,45,55,130), width=3)
    d.text((86,92), f"{index:02d}  /  08", font=font(22,True), fill=(170,180,198,210))
    d.text((86,170), title.upper(), font=font(48,True), fill=(240,242,247,255))
    d.rectangle((86,245,170,251), fill=(190,55,65,255))
    lines = textwrap.wrap(caption, width=48)
    y = 300
    for line in lines:
        d.text((86,y), line, font=font(25), fill=(210,218,230,245), stroke_width=0)
        y += 42
    d.text((86,650),"03:17  •  PSİKOLOJİK GERİLİM",font=font(17,True),fill=(125,140,160,220))
    return im

async def main():
    concat = []
    for i,(title, narration, motif) in enumerate(SCENES,1):
        audio = WORK / f"voice_{i:02d}.mp3"
        frame = WORK / f"scene_{i:02d}.png"
        clip = WORK / f"clip_{i:02d}.mp4"
        make_frame(i,title,narration,motif).save(frame)
        await edge_tts.Communicate(narration, "tr-TR-AhmetNeural", rate="-4%", pitch="-2Hz").save(str(audio))
        # Keep each visual on screen for the full spoken line, with a gentle push-in.
        probe = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)], text=True)
        duration = float(probe.strip()) + 1.8
        frames = max(24, int(duration*24))
        vf = f"zoompan=z='min(zoom+0.00035,1.055)':d=1:s={W}x{H}:fps=24,format=yuv420p"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-i",str(frame),"-i",str(audio),"-vf",vf,"-t",str(duration),"-c:v","libx264","-preset","ultrafast","-crf","22","-c:a","aac","-b:a","160k","-shortest",str(clip)],check=True)
        concat.append(clip)
    listfile = WORK / "concat.txt"
    listfile.write_text("".join(f"file '{p.as_posix()}'\n" for p in concat), encoding="utf-8")
    final = OUT / "0317_gelecekten_gelen_mesaj.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(listfile),"-c","copy","-movflags","+faststart",str(final)],check=True)
    print(f"VIDEO_READY={final}")

if __name__ == "__main__":
    asyncio.run(main())
