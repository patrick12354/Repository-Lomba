/**
 * Typical storage life by part category, from published manufacturer and industry guidance.
 * These are planning guides, not limits: sources disagree, and the datasheet of the actual product wins.
 * `months` is the cautious end of the range. A category with no entry has no published limit we could find.
 */
import { t } from "./i18n";

export type ShelfLife = { months: number; range: string; note: string; source: string; url: string };

/** Range and note are [English, Indonesian] and follow the language when read. */
const life = (months: number, range: [string, string], note: [string, string], source: string, url: string): ShelfLife => ({
  months,
  get range() {
    return t(range[0], range[1]);
  },
  get note() {
    return t(note[0], note[1]);
  },
  source,
  url,
});

export const SHELF_LIFE: Record<string, ShelfLife> = {
  GREASE: life(36, ["3 to 5 years", "3 sampai 5 tahun"], ["Unopened, in the original container", "Belum dibuka, dalam kemasan aslinya"], "Chevron, Petro-Canada, Mobil", "https://petrocanadalubricants.com/en-ca/lube-source-handbook/introduction/product-shelf-life"),
  OIL: life(60, ["about 5 years", "sekitar 5 tahun"], ["Unopened. Test it before use after that", "Belum dibuka. Setelah itu, uji dulu sebelum dipakai"], "Mobil, Chevron", "https://www.mobil.com/en/lubricants/for-businesses/industrial/industrial-faqs/industrial-lubricant-storage-and-handling"),
  BEARING: life(36, ["about 3 years", "sekitar 3 tahun"], ["The grease or preservative sets the limit", "Batasnya ditentukan oleh gemuk atau bahan pengawetnya"], "Schaeffler, SKF", "https://medias-at.schaeffler.com/mounting-and-dismounting"),
  "O-RING": life(60, ["5 to 15 years", "5 sampai 15 tahun"], ["Depends on the rubber. NBR is at the short end", "Bergantung pada jenis karetnya. NBR termasuk yang paling singkat"], "ISO 2230 summaries, SAE ARP5316", "https://www.marcorubber.com/o-ring-shelf-life.htm"),
  DIAPHRAGM: life(60, ["5 to 10 years", "5 sampai 10 tahun"], ["Depends on the rubber", "Bergantung pada jenis karetnya"], "ISO 2230 summaries, Bürkert", "https://www.burkert.com/en/Media/plm/MAN/MA/ma2030-suelasto-eu-en.pdf"),
  SEAL: life(60, ["about 5 years", "sekitar 5 tahun"], ["Inspect after 2 years in storage", "Periksa setelah 2 tahun disimpan"], "Flowserve, Pumps & Systems", "https://www.pumpsandsystems.com/what-procedures-should-i-use-when-storing-my-mechanical-seals"),
  GASKET: life(60, ["3 to 5 years", "3 sampai 5 tahun"], ["For sheet with binders. Pure PTFE and graphite last far longer", "Untuk lembaran berbahan pengikat. PTFE murni dan grafit jauh lebih awet"], "Durlon, Klinger", "https://gasketresources.com/technical-info/shelf-life-handling-storage/"),
  "FILTER ELEMENT": life(48, ["about 4 years", "sekitar 4 tahun"], ["Kept sealed and out of sunlight", "Tetap tersegel dan terlindung dari sinar matahari"], "Brackett", "https://shop.boeing.com/cpd/bdi_ba4108%3D3a"),
  CASTABLE: life(12, ["6 to 12 months", "6 sampai 12 bulan"], ["Low-cement types can be as short as 3 to 6 months", "Jenis rendah semen bisa hanya bertahan 3 sampai 6 bulan"], "Morgan Thermal Ceramics, HWI", "https://morganthermalceramics.com/media/l0iionnv/midcast_eng.pdf"),
};
