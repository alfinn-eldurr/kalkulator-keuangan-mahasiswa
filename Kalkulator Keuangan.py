"""
Kalkulator Keuangan Web (Flask)
Jalankan:  python app.py   lalu buka http://127.0.0.1:5000
"""
from flask import Flask, jsonify, request, Response
 
app = Flask(__name__)
 
 
# ---------------------------------------------------------------
# LOGIKA PERHITUNGAN (Python)
# ---------------------------------------------------------------
def num(data, key, default=0.0):
    try:
        return float(data.get(key, default))
    except (TypeError, ValueError):
        raise ValueError(f"Input '{key}' harus berupa angka.")
 
 
def hitung_investasi(d):
    """Bunga majemuk dengan setoran bulanan."""
    modal = num(d, "modal")
    setoran = num(d, "setoran")
    bunga = num(d, "bunga") / 100 / 12
    tahun = int(num(d, "tahun"))
    if tahun <= 0:
        raise ValueError("Lama investasi harus lebih dari 0 tahun.")
 
    saldo, total_setor = modal, modal
    rincian = []
    for bulan in range(1, tahun * 12 + 1):
        saldo = saldo * (1 + bunga) + setoran
        total_setor += setoran
        if bulan % 12 == 0:
            rincian.append({"tahun": bulan // 12, "setoran": total_setor, "saldo": saldo})
    return {
        "hasil": saldo,
        "total_setoran": total_setor,
        "total_bunga": saldo - total_setor,
        "rincian": rincian,
    }
 
 
def hitung_cicilan(d):
    """Cicilan pinjaman/KPR (anuitas)."""
    pokok = num(d, "pokok")
    bunga = num(d, "bunga") / 100 / 12
    bulan = int(num(d, "tahun") * 12)
    if pokok <= 0 or bulan <= 0:
        raise ValueError("Pokok pinjaman dan tenor harus lebih dari 0.")
 
    if bunga == 0:
        cicilan = pokok / bulan
    else:
        cicilan = pokok * bunga / (1 - (1 + bunga) ** -bulan)
 
    sisa, rincian = pokok, []
    bayar_pokok_thn = bayar_bunga_thn = 0.0
    for b in range(1, bulan + 1):
        bunga_b = sisa * bunga
        pokok_b = cicilan - bunga_b
        sisa -= pokok_b
        bayar_pokok_thn += pokok_b
        bayar_bunga_thn += bunga_b
        if b % 12 == 0 or b == bulan:
            rincian.append({
                "tahun": (b + 11) // 12,
                "pokok": bayar_pokok_thn,
                "bunga": bayar_bunga_thn,
                "sisa": max(sisa, 0),
            })
            bayar_pokok_thn = bayar_bunga_thn = 0.0
    total = cicilan * bulan
    return {
        "cicilan": cicilan,
        "total_bayar": total,
        "total_bunga": total - pokok,
        "rincian": rincian,
    }
 
 
def hitung_target(d):
    """Berapa yang harus ditabung per bulan untuk mencapai target."""
    target = num(d, "target")
    saat_ini = num(d, "saat_ini")
    bunga = num(d, "bunga") / 100 / 12
    bulan = int(num(d, "tahun") * 12)
    if target <= 0 or bulan <= 0:
        raise ValueError("Target dan jangka waktu harus lebih dari 0.")
 
    nilai_awal_kelak = saat_ini * (1 + bunga) ** bulan
    kekurangan = target - nilai_awal_kelak
    if kekurangan <= 0:
        perbulan = 0.0
    elif bunga == 0:
        perbulan = kekurangan / bulan
    else:
        perbulan = kekurangan * bunga / ((1 + bunga) ** bulan - 1)
    return {
        "perbulan": perbulan,
        "total_setoran": perbulan * bulan,
        "nilai_awal_kelak": nilai_awal_kelak,
    }
 
 
def hitung_inflasi(d):
    """Dampak inflasi terhadap nilai uang."""
    jumlah = num(d, "jumlah")
    inflasi = num(d, "inflasi") / 100
    tahun = num(d, "tahun")
    if jumlah <= 0 or tahun <= 0:
        raise ValueError("Jumlah dan jangka waktu harus lebih dari 0.")
    return {
        "biaya_kelak": jumlah * (1 + inflasi) ** tahun,
        "nilai_uang_kelak": jumlah / (1 + inflasi) ** tahun,
    }
 
 
KALKULATOR = {
    "investasi": hitung_investasi,
    "cicilan": hitung_cicilan,
    "target": hitung_target,
    "inflasi": hitung_inflasi,
}
 
 
@app.post("/api/<jenis>")
def api(jenis):
    fungsi = KALKULATOR.get(jenis)
    if not fungsi:
        return jsonify(error="Kalkulator tidak ditemukan."), 404
    try:
        return jsonify(fungsi(request.get_json(force=True) or {}))
    except ValueError as e:
        return jsonify(error=str(e)), 400
 
 
# ---------------------------------------------------------------
# TAMPILAN WEB (HTML + CSS + JS)
# ---------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kalkulator Keuangan</title>
<style>
  :root { --bg:#f4f6fb; --card:#fff; --text:#1f2937; --muted:#6b7280;
          --primary:#2563eb; --border:#e5e7eb; --ok:#059669; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#0f172a; --card:#1e293b; --text:#e5e7eb; --muted:#94a3b8;
            --primary:#3b82f6; --border:#334155; --ok:#34d399; } }
  * { box-sizing: border-box; }
  body { margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
         background:var(--bg); color:var(--text); }
  header { padding:28px 16px 8px; text-align:center; }
  header h1 { margin:0; font-size:1.7rem; }
  header p { margin:6px 0 0; color:var(--muted); }
  main { max-width:760px; margin:0 auto; padding:16px; }
  .tabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
  .tab { flex:1; min-width:120px; padding:10px 12px; border:1px solid var(--border);
         background:var(--card); color:var(--text); border-radius:10px; cursor:pointer;
         font-size:.95rem; }
  .tab.active { background:var(--primary); color:#fff; border-color:var(--primary); }
  .card { background:var(--card); border:1px solid var(--border); border-radius:14px;
          padding:20px; }
  .card h2 { margin-top:0; font-size:1.15rem; }
  .card .desc { color:var(--muted); margin-top:-6px; font-size:.9rem; }
  label { display:block; margin:12px 0 4px; font-size:.9rem; color:var(--muted); }
  input { width:100%; padding:10px 12px; border:1px solid var(--border); border-radius:8px;
          font-size:1rem; background:var(--bg); color:var(--text); }
  button.hitung { margin-top:18px; width:100%; padding:12px; border:0; border-radius:10px;
          background:var(--primary); color:#fff; font-size:1rem; cursor:pointer; }
  button.hitung:hover { opacity:.92; }
  .hasil { margin-top:20px; }
  .kotak { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px; }
  .item { border:1px solid var(--border); border-radius:10px; padding:12px; }
  .item small { color:var(--muted); display:block; }
  .item b { font-size:1.15rem; }
  .item.utama b { color:var(--ok); font-size:1.35rem; }
  .error { color:#dc2626; margin-top:14px; }
  .scroll { overflow-x:auto; margin-top:14px; }
  table { border-collapse:collapse; width:100%; font-size:.9rem; }
  th, td { padding:8px 10px; border-bottom:1px solid var(--border); text-align:right; white-space:nowrap; }
  th:first-child, td:first-child { text-align:left; }
  footer { text-align:center; color:var(--muted); font-size:.8rem; padding:20px; }
</style>
</head>
<body>
<header>
  <h1>💰 Kalkulator Keuangan</h1>
  <p>Rencanakan investasi, cicilan, tabungan, dan pengaruh inflasi</p>
</header>
 
<main>
  <div class="tabs" id="tabs"></div>
  <div class="card">
    <h2 id="judul"></h2>
    <p class="desc" id="desc"></p>
    <div id="form"></div>
    <button class="hitung" onclick="hitung()">Hitung</button>
    <div id="hasil" class="hasil"></div>
  </div>
</main>
<footer>Hasil hanyalah estimasi dan bukan saran keuangan.</footer>
 
<script>
const rp = n => new Intl.NumberFormat('id-ID', {style:'currency', currency:'IDR',
                 maximumFractionDigits:0}).format(n);
 
const KALKULATOR = {
  investasi: {
    nama: "Investasi", judul: "Kalkulator Investasi (Bunga Majemuk)",
    desc: "Hitung pertumbuhan uang dengan setoran rutin tiap bulan.",
    field: [
      ["modal","Modal awal (Rp)",10000000],
      ["setoran","Setoran per bulan (Rp)",1000000],
      ["bunga","Return per tahun (%)",8],
      ["tahun","Lama investasi (tahun)",10]],
    tampil: (r) => `
      <div class="kotak">
        <div class="item utama"><small>Nilai akhir</small><b>${rp(r.hasil)}</b></div>
        <div class="item"><small>Total setoran</small><b>${rp(r.total_setoran)}</b></div>
        <div class="item"><small>Total keuntungan</small><b>${rp(r.total_bunga)}</b></div>
      </div>` + tabel(["Tahun","Total Setoran","Saldo"],
        r.rincian.map(x => [x.tahun, rp(x.setoran), rp(x.saldo)]))
  },
  cicilan: {
    nama: "Cicilan / KPR", judul: "Kalkulator Cicilan Pinjaman",
    desc: "Hitung cicilan bulanan (anuitas) untuk KPR, kendaraan, atau pinjaman lain.",
    field: [
      ["pokok","Jumlah pinjaman (Rp)",500000000],
      ["bunga","Bunga per tahun (%)",9],
      ["tahun","Tenor (tahun)",15]],
    tampil: (r) => `
      <div class="kotak">
        <div class="item utama"><small>Cicilan per bulan</small><b>${rp(r.cicilan)}</b></div>
        <div class="item"><small>Total pembayaran</small><b>${rp(r.total_bayar)}</b></div>
        <div class="item"><small>Total bunga</small><b>${rp(r.total_bunga)}</b></div>
      </div>` + tabel(["Tahun","Bayar Pokok","Bayar Bunga","Sisa Pinjaman"],
        r.rincian.map(x => [x.tahun, rp(x.pokok), rp(x.bunga), rp(x.sisa)]))
  },
  target: {
    nama: "Target Tabungan", judul: "Kalkulator Target Tabungan",
    desc: "Berapa yang harus ditabung tiap bulan untuk mencapai target?",
    field: [
      ["target","Target dana (Rp)",100000000],
      ["saat_ini","Dana saat ini (Rp)",5000000],
      ["bunga","Return per tahun (%)",5],
      ["tahun","Jangka waktu (tahun)",5]],
    tampil: (r) => `
      <div class="kotak">
        <div class="item utama"><small>Tabung per bulan</small><b>${rp(r.perbulan)}</b></div>
        <div class="item"><small>Total setoran</small><b>${rp(r.total_setoran)}</b></div>
        <div class="item"><small>Dana saat ini kelak jadi</small><b>${rp(r.nilai_awal_kelak)}</b></div>
      </div>`
  },
  inflasi: {
    nama: "Inflasi", judul: "Kalkulator Inflasi",
    desc: "Lihat berapa harga barang kelak dan nilai uang Anda di masa depan.",
    field: [
      ["jumlah","Jumlah uang / harga saat ini (Rp)",100000000],
      ["inflasi","Inflasi per tahun (%)",4],
      ["tahun","Jangka waktu (tahun)",10]],
    tampil: (r) => `
      <div class="kotak">
        <div class="item utama"><small>Harga kelak (barang yang sama)</small><b>${rp(r.biaya_kelak)}</b></div>
        <div class="item"><small>Daya beli uang tersebut kelak</small><b>${rp(r.nilai_uang_kelak)}</b></div>
      </div>`
  }
};
 
function tabel(kepala, baris) {
  return `<div class="scroll"><table><thead><tr>${kepala.map(k=>`<th>${k}</th>`).join("")}</tr></thead>
    <tbody>${baris.map(b=>`<tr>${b.map(c=>`<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
 
let aktif = "investasi";
 
function render() {
  const k = KALKULATOR[aktif];
  document.getElementById("tabs").innerHTML = Object.entries(KALKULATOR).map(([id,v]) =>
    `<button class="tab ${id===aktif?'active':''}" onclick="pilih('${id}')">${v.nama}</button>`).join("");
  document.getElementById("judul").textContent = k.judul;
  document.getElementById("desc").textContent = k.desc;
  document.getElementById("form").innerHTML = k.field.map(([id,label,def]) =>
    `<label for="${id}">${label}</label><input type="number" step="any" id="${id}" value="${def}">`).join("");
  document.getElementById("hasil").innerHTML = "";
}
 
function pilih(id) { aktif = id; render(); }
 
async function hitung() {
  const k = KALKULATOR[aktif];
  const data = {};
  k.field.forEach(([id]) => data[id] = document.getElementById(id).value);
  const hasil = document.getElementById("hasil");
  try {
    const res = await fetch("/api/" + aktif, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify(data)
    });
    const json = await res.json();
    hasil.innerHTML = res.ok ? k.tampil(json) : `<p class="error">${json.error}</p>`;
  } catch (e) {
    hasil.innerHTML = `<p class="error">Gagal terhubung ke server.</p>`;
  }
}
 
render();
</script>
</body>
</html>
"""
 
 
@app.get("/")
def index():
    return Response(HTML, mimetype="text/html")
 
 
if __name__ == "__main__":
    app.run(debug=True)
 