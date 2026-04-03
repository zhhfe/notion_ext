import AppKit
import SwiftUI

struct GlassBackgroundView: NSViewRepresentable {
    let material: OverlayMaterial
    let opacity: Double
    let cornerRadius: Double

    func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.state = .active
        view.blendingMode = .behindWindow
        view.isEmphasized = true
        view.wantsLayer = true
        return view
    }

    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {
        nsView.material = material.nsMaterial
        nsView.alphaValue = opacity
        nsView.layer?.cornerRadius = cornerRadius
        nsView.layer?.masksToBounds = true
    }
}
