# =====================================================================
#  ANALISIS SLR / BIBLIOMETRIK DI R
#  Script siap-pakai untuk data yang diunduh dari aplikasi
#  "SNA Data Desa Presisi" (tab: Analisis SLR > Data & Unduh).
#
#  CARA PAKAI (RStudio / VS Code + extension R / R biasa):
#    1. Unduh dari aplikasi salah satu (atau keduanya):
#         - vosviewer_scopus.csv   (disarankan, kolom lengkap)
#         - slr_included.csv       (tabel ringkas)
#    2. Letakkan file CSV itu di folder yang SAMA dengan script ini.
#    3. Buka file ini, lalu Run/Source seluruhnya (Ctrl+Shift+S di RStudio).
#    4. Hasil (grafik PNG + tabel CSV) muncul di folder "hasil_slr/".
#
#  Script akan meng-install paket yang belum ada secara otomatis.
# =====================================================================

# ---------------------------------------------------------------------
# 0. Konfigurasi & paket
# ---------------------------------------------------------------------
options(stringsAsFactors = FALSE)

# Pindahkan working directory ke FOLDER TEMPAT SCRIPT INI berada, apa pun cara
# menjalankannya (tombol Source RStudio, source(), atau Rscript). Dengan begini
# file CSV yang diletakkan di folder yang sama otomatis ketemu — Anda tidak perlu
# setwd() manual atau lewat menu Session.
cari_folder_skrip <- function() {
  # a) Rscript ... analisis_slr.R  →  argumen --file=
  args <- commandArgs(trailingOnly = FALSE)
  m <- grep("^--file=", args, value = TRUE)
  if (length(m) > 0) return(dirname(normalizePath(sub("^--file=", "", m[1]))))
  # b) source("analisis_slr.R")  →  variabel ofile pada frame pemanggil
  for (i in seq_len(sys.nframe())) {
    of <- tryCatch(get("ofile", envir = sys.frame(i)), error = function(e) NULL)
    if (!is.null(of)) return(dirname(normalizePath(of)))
  }
  # c) tombol "Source" / editor aktif di RStudio
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    p <- tryCatch(rstudioapi::getSourceEditorContext()$path, error = function(e) "")
    if (nzchar(p)) return(dirname(normalizePath(p)))
  }
  NA_character_
}
.folder_skrip <- tryCatch(cari_folder_skrip(), error = function(e) NA_character_)
if (!is.na(.folder_skrip) && dir.exists(.folder_skrip)) {
  setwd(.folder_skrip)
  message("Working directory diset otomatis ke: ", .folder_skrip)
} else {
  message("Catatan: working directory tidak diubah (", getwd(), ").")
}

pasang_jika_perlu <- function(paket) {
  for (p in paket) {
    if (!requireNamespace(p, quietly = TRUE)) {
      message("Meng-install paket: ", p)
      install.packages(p, repos = "https://cloud.r-project.org")
    }
  }
}

# Paket inti (ringan, hampir pasti berhasil di semua OS).
pasang_jika_perlu(c("igraph"))
suppressPackageStartupMessages(library(igraph))

OUT_DIR <- "hasil_slr"
if (!dir.exists(OUT_DIR)) dir.create(OUT_DIR)

# ---------------------------------------------------------------------
# 1. Muat data — deteksi otomatis file yang tersedia
# ---------------------------------------------------------------------
baca_csv <- function(path) {
  read.csv(path, header = TRUE, check.names = FALSE,
           stringsAsFactors = FALSE, encoding = "UTF-8", na.strings = c("", "NA"))
}

if (file.exists("vosviewer_scopus.csv")) {
  message("Memuat: vosviewer_scopus.csv")
  df <- baca_csv("vosviewer_scopus.csv")
  # Peta kolom ke nama baku internal.
  kol <- list(
    penulis  = "Authors",
    tahun    = "Year",
    sumber   = "Source title",
    sitasi   = "Cited by",
    keyword  = "Author Keywords",
    negara   = "Affiliations",
    doi      = "DOI",
    judul    = "Title"
  )
} else if (file.exists("slr_included.csv")) {
  message("Memuat: slr_included.csv")
  df <- baca_csv("slr_included.csv")
  kol <- list(
    penulis  = "Penulis",
    tahun    = "Tahun",
    sumber   = "Sumber",
    sitasi   = "Sitasi",
    keyword  = "Kata Kunci",
    negara   = "Negara",
    doi      = "DOI",
    judul    = "Judul"
  )
} else {
  stop("File data tidak ditemukan di working directory saat ini:\n  ", getwd(),
       "\n\nSolusi: letakkan 'vosviewer_scopus.csv' (atau 'slr_included.csv') di ",
       "folder yang SAMA dengan script ini, lalu jalankan lagi.\n",
       "Bila file ada di folder lain, arahkan dulu dengan:\n",
       "  setwd(\"C:/path/ke/folder/berisi/csv\")\n",
       "atau menu RStudio: Session > Set Working Directory > To Source File Location.",
       call. = FALSE)
}

# Helper: ambil kolom dengan aman (kembalikan vektor kosong bila tak ada).
ambil <- function(nama) {
  if (!is.null(kol[[nama]]) && kol[[nama]] %in% names(df)) df[[kol[[nama]]]]
  else rep(NA, nrow(df))
}

# Pisah string multi-nilai bertanda "; " menjadi daftar token bersih.
pisah <- function(x) {
  x <- ifelse(is.na(x), "", as.character(x))
  lapply(strsplit(x, "\\s*;\\s*"), function(v) {
    v <- trimws(v)
    v[nzchar(v)]
  })
}

message(sprintf("Jumlah rekaman termuat: %d", nrow(df)))

# ---------------------------------------------------------------------
# 2. Tren publikasi per tahun
# ---------------------------------------------------------------------
tahun <- suppressWarnings(as.integer(ambil("tahun")))
tahun <- tahun[!is.na(tahun)]
if (length(tahun) > 0) {
  tab_tahun <- as.data.frame(table(Tahun = tahun))
  names(tab_tahun) <- c("Tahun", "Jumlah")
  tab_tahun$Tahun <- as.integer(as.character(tab_tahun$Tahun))
  tab_tahun <- tab_tahun[order(tab_tahun$Tahun), ]
  write.csv(tab_tahun, file.path(OUT_DIR, "publikasi_per_tahun.csv"), row.names = FALSE)

  png(file.path(OUT_DIR, "publikasi_per_tahun.png"), width = 1000, height = 600, res = 120)
  barplot(tab_tahun$Jumlah, names.arg = tab_tahun$Tahun,
          main = "Jumlah Publikasi per Tahun", xlab = "Tahun", ylab = "Jumlah",
          col = "#2563EB", border = NA, las = 2)
  dev.off()
  message("- publikasi_per_tahun.(csv/png) tersimpan")
}

# ---------------------------------------------------------------------
# 3. Sumber (jurnal/konferensi) teratas
# ---------------------------------------------------------------------
sumber <- ambil("sumber")
sumber <- trimws(as.character(sumber[!is.na(sumber) & nzchar(trimws(as.character(sumber)))]))
if (length(sumber) > 0) {
  tab_sumber <- sort(table(sumber), decreasing = TRUE)
  top_sumber <- head(as.data.frame(tab_sumber), 15)
  names(top_sumber) <- c("Sumber", "Jumlah")
  write.csv(top_sumber, file.path(OUT_DIR, "sumber_teratas.csv"), row.names = FALSE)
  message("- sumber_teratas.csv tersimpan")
}

# ---------------------------------------------------------------------
# 4. Kata kunci teratas
# ---------------------------------------------------------------------
kw_list <- pisah(ambil("keyword"))
semua_kw <- tolower(unlist(kw_list))
semua_kw <- semua_kw[nzchar(semua_kw)]
if (length(semua_kw) > 0) {
  tab_kw <- sort(table(semua_kw), decreasing = TRUE)
  top_kw <- head(as.data.frame(tab_kw), 25)
  names(top_kw) <- c("KataKunci", "Frekuensi")
  write.csv(top_kw, file.path(OUT_DIR, "kata_kunci_teratas.csv"), row.names = FALSE)

  png(file.path(OUT_DIR, "kata_kunci_teratas.png"), width = 1000, height = 700, res = 120)
  par(mar = c(4, 12, 3, 1))
  tk <- head(top_kw, 15)
  barplot(rev(tk$Frekuensi), names.arg = rev(tk$KataKunci), horiz = TRUE, las = 1,
          main = "15 Kata Kunci Teratas", xlab = "Frekuensi",
          col = "#059669", border = NA, cex.names = 0.8)
  dev.off()
  message("- kata_kunci_teratas.(csv/png) tersimpan")
}

# ---------------------------------------------------------------------
# 5. Jaringan ko-okurensi kata kunci (igraph)
# ---------------------------------------------------------------------
buat_jaringan_kookurensi <- function(daftar_token, min_bobot = 2,
                                      judul = "Jaringan Ko-okurensi",
                                      nama_file = "jaringan") {
  # Kumpulkan pasangan token yang muncul bersama dalam satu dokumen.
  pasangan <- list()
  for (tokens in daftar_token) {
    tokens <- unique(tolower(trimws(tokens)))
    tokens <- tokens[nzchar(tokens)]
    if (length(tokens) < 2) next
    komb <- combn(sort(tokens), 2)
    for (j in seq_len(ncol(komb))) {
      key <- paste(komb[1, j], komb[2, j], sep = "\r")
      pasangan[[key]] <- (if (is.null(pasangan[[key]])) 0 else pasangan[[key]]) + 1
    }
  }
  if (length(pasangan) == 0) {
    message("  (tidak cukup data untuk ", judul, ")")
    return(invisible(NULL))
  }
  edges <- do.call(rbind, lapply(names(pasangan), function(k) {
    ab <- strsplit(k, "\r")[[1]]
    data.frame(from = ab[1], to = ab[2], weight = pasangan[[k]])
  }))
  edges <- edges[edges$weight >= min_bobot, ]
  if (nrow(edges) == 0) {
    message("  (tidak ada pasangan dengan bobot >= ", min_bobot, " untuk ", judul, ")")
    return(invisible(NULL))
  }
  g <- graph_from_data_frame(edges, directed = FALSE)

  # Deteksi komunitas (Louvain) + centrality.
  komunitas <- cluster_louvain(g, weights = E(g)$weight)
  V(g)$komunitas <- membership(komunitas)
  V(g)$degree <- degree(g)
  V(g)$betweenness <- round(betweenness(g, weights = 1 / E(g)$weight), 3)

  # Ekspor daftar node & edge.
  node_df <- data.frame(
    Node = V(g)$name, Komunitas = V(g)$komunitas,
    Degree = V(g)$degree, Betweenness = V(g)$betweenness
  )
  node_df <- node_df[order(-node_df$Degree), ]
  write.csv(node_df, file.path(OUT_DIR, paste0(nama_file, "_node.csv")), row.names = FALSE)
  write.csv(edges,   file.path(OUT_DIR, paste0(nama_file, "_edge.csv")), row.names = FALSE)

  # Gambar jaringan.
  set.seed(42)
  png(file.path(OUT_DIR, paste0(nama_file, ".png")), width = 1200, height = 1000, res = 130)
  par(mar = c(0, 0, 2, 0))
  palet <- c("#2563EB", "#059669", "#DC2626", "#D97706", "#7C3AED",
             "#0891B2", "#DB2777", "#65A30D", "#4B5563", "#B45309")
  warna <- palet[((V(g)$komunitas - 1) %% length(palet)) + 1]
  plot(g,
       layout = layout_with_fr(g),
       vertex.size = 4 + 8 * (V(g)$degree / max(V(g)$degree)),
       vertex.color = warna, vertex.frame.color = NA,
       vertex.label = V(g)$name, vertex.label.cex = 0.7,
       vertex.label.color = "#111827", vertex.label.dist = 0.4,
       edge.width = 0.5 + 2 * (E(g)$weight / max(E(g)$weight)),
       edge.color = "#CBD5E1",
       main = judul)
  dev.off()
  message("- ", nama_file, ".(png) + node/edge.csv tersimpan (",
          vcount(g), " node, ", ecount(g), " edge, ",
          length(komunitas), " komunitas)")
  invisible(g)
}

# 5a. Jaringan ko-kata kunci.
buat_jaringan_kookurensi(kw_list, min_bobot = 2,
                         judul = "Jaringan Ko-okurensi Kata Kunci",
                         nama_file = "jaringan_kata_kunci")

# 5b. Jaringan ko-penulis (co-authorship).
au_list <- pisah(ambil("penulis"))
buat_jaringan_kookurensi(au_list, min_bobot = 2,
                         judul = "Jaringan Ko-penulis (Co-authorship)",
                         nama_file = "jaringan_penulis")

# ---------------------------------------------------------------------
# 6. (Opsional) Analisis lengkap dengan paket 'bibliometrix'
#    Hanya berjalan pada vosviewer_scopus.csv (format Scopus).
#    Jika paket gagal di-install, script tetap selesai tanpa error.
# ---------------------------------------------------------------------
if (file.exists("vosviewer_scopus.csv")) {
  ok <- tryCatch({
    pasang_jika_perlu("bibliometrix")
    TRUE
  }, error = function(e) FALSE)

  if (ok && requireNamespace("bibliometrix", quietly = TRUE)) {
    tryCatch({
      suppressPackageStartupMessages(library(bibliometrix))
      M <- convert2df("vosviewer_scopus.csv", dbsource = "scopus", format = "csv")
      hasil <- biblioAnalysis(M)
      ringkasan <- capture.output(summary(hasil, k = 15, pause = FALSE))
      writeLines(ringkasan, file.path(OUT_DIR, "bibliometrix_ringkasan.txt"))
      message("- bibliometrix_ringkasan.txt tersimpan")
      message("  Tip: jalankan biblioshiny() untuk dashboard interaktif bibliometrix.")
    }, error = function(e) {
      message("  (bibliometrix dilewati: ", conditionMessage(e), ")")
    })
  } else {
    message("  (bibliometrix tidak terpasang — bagian ini dilewati, analisis inti tetap lengkap)")
  }
}

message("\nSELESAI. Semua keluaran ada di folder: ", normalizePath(OUT_DIR))
