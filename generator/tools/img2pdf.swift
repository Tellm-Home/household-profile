import Foundation; import CoreGraphics
// usage: [PDF_TITLE=...] img2pdf out.pdf pageWidthPx pageHeightPx slice0.jpg slice1.jpg ... (slices stacked top to bottom, 2x)
let a = CommandLine.arguments; let k: CGFloat = 0.75
var box = CGRect(x: 0, y: 0, width: CGFloat(Double(a[2])!) * k, height: CGFloat(Double(a[3])!) * k)
let ctx = CGContext(URL(fileURLWithPath: a[1]) as CFURL, mediaBox: &box, [kCGPDFContextTitle as String: ProcessInfo.processInfo.environment["PDF_TITLE"] ?? "Household profile", kCGPDFContextCreator as String: "M"] as CFDictionary)!
ctx.beginPDFPage(nil)
var top = box.height
for p in a[4...] {
  let img = CGImage(jpegDataProviderSource: CGDataProvider(url: URL(fileURLWithPath: p) as CFURL)!, decode: nil, shouldInterpolate: true, intent: .defaultIntent)!
  let w = box.width, h = CGFloat(img.height) / CGFloat(img.width) * w
  ctx.draw(img, in: CGRect(x: 0, y: top - h, width: w, height: h)); top -= h
}
ctx.endPDFPage(); ctx.closePDF()
