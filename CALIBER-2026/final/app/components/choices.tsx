import { ChevronDown } from "lucide-react";
import { Panel, PanelHead } from "./ui";
import { t } from "@/lib/i18n";

type Choice = { q: string; did: string; why: string };

/**
 * Every choice a judge might question, with what we did and why. Kept in one place so a gap we already
 * checked and closed is answered on the page instead of re-opened in the room.
 */
const GROUPS_EN: { title: string; items: Choice[] }[] = [
  {
    title: "Forecast",
    items: [
      {
        q: "Why no seasonal pattern?",
        did: "We do not fit a calendar season. The turnaround, the one big swing, is planned as its own event.",
        why: "The data covers 17 months, so every month appears once or twice. One cycle cannot separate a season from a one-off. A season can enter the model once two to three years of data exist.",
      },
      {
        q: "Why not deep learning?",
        did: "Two gradient-boosted models (will it be used, and how much) plus a simulation of many possible futures.",
        why: "The data is a table of 17 months and 74% of parts have no use on record. Sequence models need long histories per part. The simpler model beat the comparison methods on months it never saw.",
      },
      {
        q: "Do maintenance plans and breakdown notices feed the model?",
        did: "Partly. The model scores how many notifications, emergency notifications and maintenance items each part's equipment has. The timing signals (maintenance due soon, open backlog, open requests) are shown next to each part as context, not used to score.",
        why: "We tested 12 extra timing and context signals one by one. None improved the score, because installed base and history already carry the same information. In this data a notification on a machine does not raise part use there soon after: 31.8% of parts were drawn within 30 days of a notification, against 31.1% in a random month. The maintenance files also list no parts, so a plan cannot be turned directly into a part quantity.",
      },
      {
        q: "What about production rate and operating conditions?",
        did: "Not modelled directly, because none of the six files holds them. The nearest signal is the plant-wide level of use over the last 90 days, plus the Size control for the turnaround. Running hours and throughput per machine are the first extra data we propose.",
        why: "Parts that wear with use follow hours run, not the calendar, so this data can warn earlier and tell a busy machine from an idle one. It comes from the plant's own process historian, so it needs no new sensors. It enters the model only if it beats today's score on the same replay, the same test every other signal had to pass.",
      },
      {
        q: "Why not read the notification text to guess the part?",
        did: "Dropped.",
        why: "Matching notification text to parts scored 0.376, below simply picking the most used parts (0.497).",
      },
      {
        q: "The model uses today's Min and Max. Is that a leak?",
        did: "Kept as an input, and the version without them is shown beside every score.",
        why: "In real use the planner's Min and Max are known when the forecast is made. Without them the scores are 89 for all parts and 77 for parts with no use, still ahead of the simple rule.",
      },
      {
        q: "Is the AI worth it over a simple re-tune?",
        did: "The replay also runs the best non-AI option: the same targets and delivery times, with the classic formula from the last 180 days of use, refreshed every month like ours.",
        why: "Re-tuning alone already lifts availability, so it is the fair test. On critical stocked parts it reaches 93% with Rp 1,066 billion of stock and 3,490 empty-shelf days. Sparekit reaches 98% with Rp 310 billion and 2,239 days. Part of the gap is that a formula built on history has nothing to go on for parts with no recent use, so those keep today's limits.",
      },
      {
        q: "Why does it not predict exact units?",
        did: "Stock limits come from the range of likely use during delivery at each part's target, not from one number.",
        why: "On units the model is level with assuming the last 90 days repeat. Spare part use is too sparse for exact counts, so we plan on the range and prove it on the replay of real use.",
      },
    ],
  },
  {
    title: "Stock and money",
    items: [
      {
        q: "Which rupiah figures can be compared?",
        did: "Today's position (above Max, to buy, to release, on the shelf) counts only parts with a purchase-order price. Plan comparisons (What if, replay) price every part, using the median price of the same part type where there is no order.",
        why: "Only about 1 in 6 parts has a real price. Real prices keep today's figures honest. Comparing plans needs every part priced, or the cheapest plan would simply be the one that stocks unpriced parts. The two kinds are never set against each other.",
      },
      {
        q: "Is all of the Rp 414 billion above Max cash we can free?",
        did: "No. It is the value above today's Max in SAP. Two A parts that were never used in 17 months hold Rp 254 billion of it, 61%: a thrust pad (Rp 163 billion) and a rotor blade (Rp 91 billion). They are marked to stop buying and to check. The part we can release with little risk is the Rp 56.9 billion of less critical stock.",
        why: "A critical part with no use may still be insurance, so a person checks it before anything is cut. The To do board shows a second figure, Rp 443 billion, measured against our new Max instead of SAP's, so it answers a different question. The Above Max line in Stock health is smaller because each part sits in one group only, and most of the excess is on parts in the Unused group.",
      },
      {
        q: "Why do we quote availability only from the replay?",
        did: "The one availability figure is the replay of real use from March to September 2026, on the 495 critical stocked parts that were used: on the shelf for 53% of requests today, 98% with our limits.",
        why: "The What if chart is a model of a settled plan. Its per-cycle availability averages over every A part, including the many that are never used, so it reads high. The replay counts real requests, so it is the figure to trust.",
      },
      {
        q: "Why is the stock saving 59% on What if but 69% in the replay?",
        did: "Both are shown, each labelled. The replay is the one to quote.",
        why: "What if models every part once a plan has settled, including Non Stock parts the plan would start to hold. The replay covers parts already kept in stock, on seven months of real use. Its availability is measured on the 495 critical parts that were used, and its stock value on all 3,656 stocked parts.",
      },
      {
        q: "Does the stock saving turn into cash right away?",
        did: "No. The replay starts every plan at its own Max, as if the excess were already gone. Stop buying only prevents new excess.",
        why: "From the shelf on record, availability still rises from 60% to 93%, but stock stays about the same until the excess is returned, moved to a twin part or written off. That is a decision for the plant, so we list what to release and leave it to a person. The shelf on record was read after these months, so this is a rough guide.",
      },
      {
        q: "Why does stock value on priced parts go up in the replay?",
        did: "Shown openly on the Forecast page.",
        why: "Money moves out of idle parts and into the parts that are really used, and those are the ones with purchase orders. On the 495 used critical parts alone, stock rises from Rp 31 billion to Rp 136 billion. Across all 3,656 stocked parts it still falls 69%, because most of the money sits in idle parts.",
      },
      {
        q: "Why are empty Non Stock parts not counted as gaps?",
        did: "Critical parts that are empty are counted among Stock Items only, and the replay leaves Non Stock parts out for the same reason.",
        why: "A Non Stock part is bought for each job, so an empty shelf is its normal state. The organisers confirmed Non Stock is the current setting and may be changed. We suggest moving turnaround parts to Stock where the delivery time is long. If critical Non Stock parts were all kept on the shelf, availability across all critical parts used would be 95%, with Rp 782 billion of stock.",
      },
      {
        q: "What makes the stock limits dynamic?",
        did: "The model retrains on the first of each month, using only what has happened so far, and sets new limits. The Replay page plays this back month by month.",
        why: "Between 740 and 1,668 stocked parts got new limits each month, in both directions: in June most Mins went down, in July most went up. Against setting limits once, it leaves 15% fewer empty-shelf days for 2% more stock, with about the same availability.",
      },
      {
        q: "Why does the buying list include Non Stock parts?",
        did: "Rp 130.9 billion of suggested buying splits three ways: Rp 49.8 billion for parts kept in stock, Rp 33.3 billion for Non Stock parts the next turnaround needs, and Rp 47.8 billion for Non Stock parts the forecast expects to be used. Those last ones carry a note on the board, and Send to SAP has a file listing them.",
        why: "A Non Stock part is bought per job, so holding one means changing it to a Stock Item first. The organisers allow that, but it is the plant's call, so we suggest it and do not assume it. The replay headline counts stocked parts only. The wider run that keeps all critical Non Stock parts on the shelf reaches 95% with Rp 782 billion of stock.",
      },
      {
        q: "Where does the cost of a shortage come from?",
        did: "It is a slider on What if, set at Rp 5 million for one A part missing for one day. B counts 30%, C 5%, S 1%.",
        why: "No downtime cost is in the data and we did not invent one. It is the cost of one missing part, not of the whole plant stopping, since one part rarely stops a plant. The Recommended plan holds less stock and runs out less than today, so it is cheaper at any setting.",
      },
      {
        q: "Why not claim rush orders cost more?",
        did: "Dropped. We only say rush requests arrive late far more often (92.5% against 52.9%).",
        why: "The unit price of rush and normal orders is the same (ratio 1.00). A claim that most rush orders were avoidable did not hold either: the same test gave the same result on normal orders.",
      },
    ],
  },
  {
    title: "Data and scope",
    items: [
      {
        q: "Where does the turnaround date come from?",
        did: "1 June 2027, as an editable planning assumption.",
        why: "No date is in the data, and an official schedule is not public. The last turnaround ran November 2025 to January 2026. Change the date on the Plant map and every number follows.",
      },
      {
        q: "Some delivery times are over a year. Is that right?",
        did: "Kept as recorded, and labelled as the slow case on each part.",
        why: "Delivery time runs from request date to the delivery date on the order. For turnaround parts that date can be set months ahead on purpose, which would stretch it. Cutting long values ourselves would hide real risk, so we keep them, plan on the slow case, and leave the date question to the plant's procurement team.",
      },
      {
        q: "Pumps come in pairs (A and B). Does a spare unit lower the risk?",
        did: "Shown on each part as a standby unit, without lowering its criticality.",
        why: "Criticality comes from the plant's own functional locations, and the organisers set its order (A, B, C, S). A standby pump keeps the plant running, but it also has to be repaired before it fails too. We leave that call to the planner.",
      },
      {
        q: "Why does the turnaround list copy the last turnaround?",
        did: "The last turnaround's actual use is the starting kit, scaled by the Size control.",
        why: "There is one turnaround in the data, so its real use is the best evidence of the next one. Each later turnaround is planned to update the kit with what was really used (see how Sparekit keeps learning).",
      },
      {
        q: "Why are duplicate parts only suggested, not merged?",
        did: "Parts that look identical are offered as a source before buying, with a confirm step.",
        why: "The descriptions match, but 25 of the 57 groups sit on the same machine, so they may be separate positions. A person has to confirm they can replace each other.",
      },
      {
        q: "Why does the demo reset?",
        did: "Decisions are written to a SQLite database on the server; analysis reads a second, read-only SQLite file.",
        why: "The hosting keeps files only while a server is warm. In production the same tables sit on the plant's own database.",
      },
    ],
  },
];

const GROUPS_ID: { title: string; items: Choice[] }[] = [
  {
    title: "Prakiraan",
    items: [
      {
        q: "Mengapa tidak ada pola musiman?",
        did: "Kami tidak memasang pola musim kalender. Turnaround, satu-satunya lonjakan besar, direncanakan sebagai kejadian tersendiri.",
        why: "Data hanya mencakup 17 bulan, sehingga setiap bulan muncul sekali atau dua kali. Satu siklus tidak cukup untuk membedakan pola musiman dari kejadian sekali. Pola musiman baru bisa masuk ke model setelah ada data dua sampai tiga tahun.",
      },
      {
        q: "Mengapa tidak memakai deep learning?",
        did: "Dua model gradient boosting (akan terpakai atau tidak, dan berapa banyak) ditambah simulasi berbagai kemungkinan masa depan.",
        why: "Datanya berupa tabel 17 bulan, dan 74% suku cadang tidak memiliki catatan pemakaian. Model sekuensial membutuhkan riwayat panjang untuk setiap suku cadang. Model yang lebih sederhana ini mengungguli metode pembanding pada bulan-bulan yang belum pernah dilihatnya.",
      },
      {
        q: "Apakah rencana pemeliharaan dan laporan kerusakan masuk ke model?",
        did: "Sebagian. Model menilai jumlah laporan, laporan darurat, dan item pemeliharaan pada peralatan tempat suku cadang terpasang. Sinyal waktu (pemeliharaan yang segera jatuh tempo, laporan yang masih terbuka, permintaan yang masih terbuka) ditampilkan di samping setiap suku cadang sebagai konteks, tetapi tidak dipakai untuk menilai.",
        why: "Kami menguji 12 sinyal waktu dan konteks tambahan satu per satu. Tidak ada yang memperbaiki skor, karena basis terpasang dan riwayat pemakaian sudah memuat informasi yang sama. Dalam data ini, laporan pada sebuah mesin tidak menaikkan pemakaian suku cadang di sana dalam waktu dekat: 31,8% suku cadang diambil dalam 30 hari setelah ada laporan, dibandingkan 31,1% pada bulan acak. Berkas pemeliharaan juga tidak mencantumkan suku cadang, sehingga rencana tidak bisa langsung diubah menjadi jumlah suku cadang.",
      },
      {
        q: "Bagaimana dengan laju produksi dan kondisi operasi?",
        did: "Tidak dimodelkan langsung, karena tidak ada di enam berkas data. Sinyal terdekat adalah tingkat pemakaian seluruh kilang dalam 90 hari terakhir, ditambah pengatur Ukuran untuk turnaround. Jam operasi dan throughput per mesin adalah data tambahan pertama yang kami usulkan.",
        why: "Suku cadang yang aus karena dipakai mengikuti jam operasi, bukan kalender, sehingga data ini bisa memberi peringatan lebih awal dan membedakan mesin yang sibuk dari yang menganggur. Datanya berasal dari process historian milik kilang, jadi tidak perlu sensor baru. Data ini baru masuk ke model kalau mengalahkan skor saat ini pada simulasi ulang yang sama, yaitu uji yang juga harus dilewati sinyal lain.",
      },
      {
        q: "Mengapa teks laporan kerusakan tidak dibaca untuk menebak suku cadangnya?",
        did: "Tidak dipakai.",
        why: "Pencocokan teks laporan kerusakan dengan suku cadang hanya mendapat skor 0,376, lebih rendah daripada sekadar memilih suku cadang yang paling sering dipakai (0,497).",
      },
      {
        q: "Model memakai Min dan Max saat ini. Apakah itu kebocoran data?",
        did: "Tetap dipakai sebagai masukan, dan versi tanpa keduanya ditampilkan di samping setiap skor.",
        why: "Dalam praktiknya, Min dan Max dari perencana sudah diketahui saat prakiraan dibuat. Tanpa keduanya, skornya 89 untuk semua suku cadang dan 77 untuk suku cadang tanpa pemakaian, tetap lebih baik daripada aturan sederhana.",
      },
      {
        q: "Apakah AI sepadan dibandingkan penyetelan ulang sederhana?",
        did: "Simulasi ulang juga menjalankan opsi non-AI terbaik: target dan waktu kirim yang sama, dengan rumus klasik dari pemakaian 180 hari terakhir, diperbarui setiap bulan seperti milik kami.",
        why: "Penyetelan ulang saja sudah menaikkan ketersediaan, jadi itulah pembanding yang adil. Pada suku cadang kritis yang distok, cara ini mencapai 93% dengan stok Rp1.066 miliar dan 3.490 hari rak kosong. Sparekit mencapai 98% dengan Rp310 miliar dan 2.239 hari. Sebagian selisihnya karena rumus berbasis riwayat tidak punya dasar untuk suku cadang yang belakangan tidak terpakai, sehingga batasnya tetap seperti saat ini.",
      },
      {
        q: "Mengapa model tidak memprakirakan jumlah unit secara persis?",
        did: "Batas stok ditentukan dari rentang pemakaian yang mungkin terjadi selama masa pengiriman pada target tiap suku cadang, bukan dari satu angka.",
        why: "Untuk jumlah unit, model setara dengan asumsi bahwa 90 hari terakhir terulang. Pemakaian suku cadang terlalu jarang untuk dihitung secara persis, jadi kami merencanakan berdasarkan rentang dan membuktikannya lewat simulasi ulang pemakaian riil.",
      },
    ],
  },
  {
    title: "Stok dan uang",
    items: [
      {
        q: "Angka rupiah mana yang bisa dibandingkan?",
        did: "Posisi hari ini (di atas Max, perlu dibeli, perlu dilepas, di rak) hanya menghitung suku cadang yang memiliki harga pesanan pembelian. Perbandingan rencana (Simulasi, simulasi ulang) memberi harga pada setiap suku cadang, memakai harga median jenis suku cadang yang sama jika belum pernah dipesan.",
        why: "Hanya sekitar 1 dari 6 suku cadang yang memiliki harga riil. Harga riil menjaga angka hari ini tetap jujur. Perbandingan rencana membutuhkan harga untuk setiap suku cadang; jika tidak, rencana termurah hanyalah rencana yang menyetok suku cadang tanpa harga. Kedua jenis angka ini tidak pernah diadu satu sama lain.",
      },
      {
        q: "Apakah seluruh Rp414 miliar di atas Max adalah uang yang bisa dibebaskan?",
        did: "Tidak. Angka itu adalah nilai di atas Max SAP saat ini. Dua suku cadang A yang tidak pernah dipakai selama 17 bulan memegang Rp254 miliar di antaranya, atau 61%: thrust pad (Rp163 miliar) dan rotor blade (Rp91 miliar). Keduanya ditandai untuk dihentikan pembeliannya dan diperiksa. Bagian yang bisa dilepas dengan risiko kecil adalah Rp56,9 miliar stok yang kurang kritis.",
        why: "Suku cadang kritis yang tidak terpakai bisa saja merupakan cadangan pengaman, jadi harus diperiksa orang sebelum dipotong. Papan Tugas menampilkan angka kedua, Rp443 miliar, yang diukur terhadap Max baru kami, bukan Max SAP, sehingga menjawab pertanyaan yang berbeda. Baris Di atas Max pada Kesehatan stok lebih kecil karena setiap suku cadang hanya masuk satu kelompok, dan sebagian besar kelebihannya ada pada suku cadang di kelompok tidak terpakai.",
      },
      {
        q: "Mengapa angka ketersediaan hanya diambil dari simulasi ulang?",
        did: "Satu-satunya angka ketersediaan berasal dari simulasi ulang pemakaian riil Maret sampai September 2026, pada 495 suku cadang kritis yang distok dan terpakai: tersedia di rak untuk 53% permintaan saat ini, dan 98% dengan batas stok kami.",
        why: "Grafik Simulasi adalah model rencana yang sudah stabil. Ketersediaan per siklusnya dirata-ratakan atas semua suku cadang A, termasuk banyak yang tidak pernah terpakai, sehingga angkanya tampak tinggi. Simulasi ulang menghitung permintaan riil, jadi angka itulah yang layak dipercaya.",
      },
      {
        q: "Mengapa penghematan stok 59% di Simulasi, tetapi 69% di simulasi ulang?",
        did: "Keduanya ditampilkan dengan labelnya masing-masing. Angka simulasi ulang yang dikutip.",
        why: "Simulasi memodelkan semua suku cadang setelah rencana stabil, termasuk suku cadang Non Stock yang akan mulai disimpan. Simulasi ulang mencakup suku cadang yang sudah distok, pada tujuh bulan pemakaian riil. Ketersediaannya diukur pada 495 suku cadang kritis yang terpakai, dan nilai stoknya pada seluruh 3.656 suku cadang yang distok.",
      },
      {
        q: "Apakah penghematan stok langsung menjadi uang?",
        did: "Tidak. Simulasi ulang memulai setiap rencana pada Max-nya sendiri, seolah kelebihannya sudah hilang. Menghentikan pembelian hanya mencegah kelebihan baru.",
        why: "Jika dimulai dari rak yang tercatat, ketersediaan tetap naik dari 60% menjadi 93%, tetapi stok kurang lebih tetap sampai kelebihannya diretur, dipindahkan ke suku cadang kembar, atau dihapus. Itu keputusan kilang, jadi kami mendaftar apa yang bisa dilepas dan menyerahkannya kepada orang. Catatan rak itu dibaca setelah bulan-bulan ini, jadi angkanya hanya panduan kasar.",
      },
      {
        q: "Mengapa nilai stok suku cadang berharga naik di simulasi ulang?",
        did: "Ditampilkan secara terbuka di halaman Prakiraan.",
        why: "Uang berpindah dari suku cadang yang menganggur ke suku cadang yang benar-benar dipakai, dan justru suku cadang inilah yang memiliki pesanan pembelian. Khusus 495 suku cadang kritis yang terpakai, stok naik dari Rp31 miliar menjadi Rp136 miliar. Di seluruh 3.656 suku cadang yang distok, stok tetap turun 69%, karena sebagian besar uang tertanam di suku cadang yang menganggur.",
      },
      {
        q: "Mengapa suku cadang Non Stock yang kosong tidak dihitung sebagai kekurangan?",
        did: "Suku cadang kritis yang kosong hanya dihitung di antara Stock Item, dan simulasi ulang juga tidak menghitung suku cadang Non Stock dengan alasan yang sama.",
        why: "Suku cadang Non Stock dibeli untuk setiap pekerjaan, jadi rak kosong adalah keadaan normalnya. Panitia menegaskan bahwa Non Stock adalah pengaturan saat ini dan boleh diubah. Kami menyarankan agar suku cadang turnaround dengan waktu kirim yang lama dipindahkan ke Stock. Jika semua suku cadang Non Stock kritis disimpan di rak, ketersediaan seluruh suku cadang kritis yang terpakai menjadi 95%, dengan stok Rp782 miliar.",
      },
      {
        q: "Apa yang membuat batas stok dinamis?",
        did: "Model dilatih ulang setiap tanggal 1, hanya dengan kejadian sampai saat itu, lalu menetapkan batas baru. Halaman Simulasi ulang memutarnya bulan demi bulan.",
        why: "Setiap bulan, 740 sampai 1.668 suku cadang stok mendapat batas baru, ke dua arah: pada Juni kebanyakan Min turun, pada Juli kebanyakan naik. Dibandingkan menetapkan batas sekali, cara ini menyisakan 15% lebih sedikit hari rak kosong dengan stok 2% lebih banyak, dan ketersediaan kurang lebih sama.",
      },
      {
        q: "Mengapa daftar beli memuat suku cadang Non Stock?",
        did: "Usulan pembelian Rp130,9 miliar terbagi tiga: Rp49,8 miliar untuk suku cadang yang distok, Rp33,3 miliar untuk suku cadang Non Stock yang dibutuhkan turnaround berikutnya, dan Rp47,8 miliar untuk suku cadang Non Stock yang menurut prakiraan akan terpakai. Yang terakhir diberi catatan di papan Tugas, dan Kirim ke SAP memiliki berkas daftarnya.",
        why: "Suku cadang Non Stock dibeli per pekerjaan, jadi menyimpannya berarti mengubahnya menjadi Stock Item lebih dulu. Panitia mengizinkan hal itu, tetapi keputusannya ada di kilang, jadi kami menyarankannya tanpa menganggapnya sudah terjadi. Angka utama simulasi ulang hanya menghitung suku cadang yang distok. Simulasi yang lebih luas, dengan semua suku cadang Non Stock kritis disimpan di rak, mencapai 95% dengan stok Rp782 miliar.",
      },
      {
        q: "Dari mana biaya kekurangan stok berasal?",
        did: "Berupa penggeser di halaman Simulasi, diatur Rp5 juta untuk satu suku cadang A yang tidak tersedia selama satu hari. B dihitung 30%, C 5%, S 1%.",
        why: "Data tidak memuat biaya henti operasi, dan kami tidak mengarangnya. Angka ini adalah biaya satu suku cadang yang tidak tersedia, bukan biaya seluruh kilang berhenti, karena satu suku cadang jarang menghentikan kilang. Rencana yang Disarankan menyimpan stok lebih sedikit dan lebih jarang kehabisan stok daripada saat ini, sehingga lebih murah pada pengaturan berapa pun.",
      },
      {
        q: "Mengapa tidak mengklaim pesanan percepatan lebih mahal?",
        did: "Tidak dipakai. Kami hanya menyatakan bahwa permintaan percepatan jauh lebih sering terlambat (92,5% dibandingkan 52,9%).",
        why: "Harga satuan pesanan percepatan dan pesanan biasa sama (rasio 1,00). Klaim bahwa sebagian besar pesanan percepatan sebenarnya bisa dihindari juga tidak terbukti: uji yang sama memberi hasil serupa pada pesanan biasa.",
      },
    ],
  },
  {
    title: "Data dan cakupan",
    items: [
      {
        q: "Dari mana tanggal turnaround berasal?",
        did: "1 Juni 2027, sebagai asumsi perencanaan yang bisa diubah.",
        why: "Data tidak memuat tanggal, dan jadwal resminya tidak dipublikasikan. Turnaround terakhir berlangsung November 2025 sampai Januari 2026. Ubah tanggalnya di Peta kilang, dan semua angka akan menyesuaikan.",
      },
      {
        q: "Ada waktu kirim yang lebih dari setahun. Apakah itu benar?",
        did: "Tetap dipakai sesuai catatan, dan diberi label skenario lambat pada setiap suku cadang.",
        why: "Waktu kirim dihitung dari tanggal permintaan sampai tanggal pengiriman di pesanan. Untuk suku cadang turnaround, tanggal itu bisa sengaja ditetapkan berbulan-bulan ke depan, sehingga waktunya memanjang. Memotong nilai yang panjang sendiri justru menyembunyikan risiko nyata, jadi kami mempertahankannya, merencanakan dengan skenario lambat, dan menyerahkan pertanyaan tanggal itu kepada tim pengadaan kilang.",
      },
      {
        q: "Pompa dipasang berpasangan (A dan B). Apakah unit cadangan menurunkan risikonya?",
        did: "Ditampilkan pada setiap suku cadang sebagai unit siaga, tanpa menurunkan kekritisannya.",
        why: "Kekritisan berasal dari lokasi fungsional kilang itu sendiri, dan panitia menetapkan urutannya (A, B, C, S). Pompa siaga memang menjaga kilang tetap beroperasi, tetapi pompa itu juga harus diperbaiki sebelum ikut rusak. Keputusan itu kami serahkan kepada perencana.",
      },
      {
        q: "Mengapa daftar turnaround menyalin turnaround terakhir?",
        did: "Pemakaian riil pada turnaround terakhir menjadi paket awal, yang diskalakan dengan pengatur Ukuran.",
        why: "Hanya ada satu turnaround dalam data, jadi pemakaian riilnya adalah bukti terbaik untuk turnaround berikutnya. Setiap turnaround selanjutnya direncanakan memperbarui paket dengan pemakaian yang sebenarnya (lihat cara Sparekit terus belajar).",
      },
      {
        q: "Mengapa suku cadang kembar hanya disarankan, tidak digabung?",
        did: "Suku cadang yang tampak identik ditawarkan sebagai sumber sebelum membeli, dengan langkah konfirmasi.",
        why: "Deskripsinya cocok, tetapi 25 dari 57 kelompok berada di mesin yang sama, sehingga bisa jadi posisinya berbeda. Harus ada orang yang memastikan keduanya memang bisa saling menggantikan.",
      },
      {
        q: "Mengapa demo ini bisa ter-reset?",
        did: "Keputusan ditulis ke basis data SQLite di server; analisis membaca berkas SQLite kedua yang hanya bisa dibaca.",
        why: "Layanan hosting hanya menyimpan berkas selama server masih aktif. Di lingkungan produksi, tabel yang sama berada di basis data milik kilang sendiri.",
      },
    ],
  },
];

export function Choices() {
  return (
    <Panel>
      <PanelHead title={t("Choices we made, and why", "Pilihan yang kami ambil, dan alasannya")} />
      <p className="m-0 px-5 pt-1 text-[13px] leading-[1.5] text-ink-2">{t("The questions we asked ourselves, what we did, and what we chose not to do. Press one to open it.", "Pertanyaan yang kami ajukan kepada diri sendiri, yang kami lakukan, dan yang sengaja tidak kami lakukan. Tekan salah satunya untuk membukanya.")}</p>
      <div className="grid grid-cols-1 gap-x-8 px-5 pb-4 pt-2 lg:grid-cols-3">
        {t(GROUPS_EN, GROUPS_ID).map((g) => (
          <div key={g.title}>
            <h3 className="m-0 border-b border-line py-2 text-[12px] font-semibold uppercase tracking-[0.04em] text-ink-3">{g.title}</h3>
            {g.items.map((c) => (
              <details key={c.q} className="group border-b border-line py-2 text-[13px]">
                <summary className="flex cursor-pointer list-none items-start justify-between gap-3 font-medium [&::-webkit-details-marker]:hidden">
                  {c.q}
                  <ChevronDown aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-ink-3 transition-transform duration-150 group-open:rotate-180" />
                </summary>
                <p className="m-0 mt-1.5 leading-[1.5] text-ink"><span className="font-semibold">{t("What we did: ", "Yang kami lakukan: ")}</span>{c.did}</p>
                <p className="m-0 mt-1 leading-[1.5] text-ink-2"><span className="font-semibold text-ink">{t("Why: ", "Alasannya: ")}</span>{c.why}</p>
              </details>
            ))}
          </div>
        ))}
      </div>
    </Panel>
  );
}
