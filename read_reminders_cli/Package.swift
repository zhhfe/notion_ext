// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "read_reminders_cli",
    platforms: [.macOS(.v11)],
    products: [
        .executable(name: "read_reminders_cli", targets: ["read_reminders_cli"])
    ],
    targets: [
        .executableTarget(
            name: "read_reminders_cli",
            path: "Sources"
        )
    ]
)
