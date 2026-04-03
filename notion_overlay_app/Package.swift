// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NotionOverlayApp",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "NotionOverlayApp", targets: ["NotionOverlayApp"])
    ],
    targets: [
        .executableTarget(
            name: "NotionOverlayApp",
            path: "Sources/NotionOverlayApp",
            linkerSettings: [
                .linkedFramework("AppKit"),
                .linkedFramework("Carbon"),
                .linkedFramework("ServiceManagement"),
            ]
        ),
    ]
)
