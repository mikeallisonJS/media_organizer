import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  BookOpen,
  FileAudio,
  FileImage,
  FileVideo,
  Github,
  Twitter,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Image
              src="/logo.png"
              alt="Archimedius Logo"
              width={32}
              height={32}
              className="rounded"
            />
            <span className="text-xl font-bold">Archimedius</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="#features"
              className="text-sm font-medium hover:text-primary"
            >
              Features
            </Link>
            <Link
              href="#how-it-works"
              className="text-sm font-medium hover:text-primary"
            >
              How It Works
            </Link>
            <Link
              href="#download"
              className="text-sm font-medium hover:text-primary"
            >
              Download
            </Link>
          </nav>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" className="hidden md:flex">
              Documentation
            </Button>
            <Button size="sm">Download</Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48 bg-gradient-to-b from-blue-950 to-background">
          <div className="container px-4 md:px-6">
            <div className="grid gap-6 lg:grid-cols-2 lg:gap-12 xl:grid-cols-2">
              <div className="flex flex-col justify-center space-y-4">
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none">
                    Organize Your Media Files{" "}
                    <span className="text-blue-400">Intelligently</span>
                  </h1>
                  <p className="max-w-[600px] text-muted-foreground md:text-xl">
                    Archimedius extracts metadata from your audio, video,
                    images, and ebooks to organize them into a structured
                    directory hierarchy.
                  </p>
                </div>
                <div className="flex flex-col gap-2 min-[400px]:flex-row">
                  <Button className="inline-flex h-10 items-center justify-center bg-blue-600 hover:bg-blue-700">
                    Download Now
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    className="inline-flex h-10 items-center justify-center"
                  >
                    View Documentation
                  </Button>
                </div>
              </div>
              <div className="flex items-center justify-center">
                <Image
                  src="/screenshot.png"
                  width={500}
                  height={400}
                  alt="Archimedius Application Screenshot"
                  className="rounded-lg shadow-xl"
                  priority
                />
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="w-full py-12 md:py-24 lg:py-32">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <div className="inline-block rounded-lg bg-blue-900 px-3 py-1 text-sm text-blue-300">
                  Features
                </div>
                <h2 className="text-3xl font-bold tracking-tighter md:text-4xl/tight">
                  Powerful Media Organization
                </h2>
                <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Archimedius helps you organize your media files based on their
                  metadata, creating a structured and logical file system.
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl items-center gap-6 py-12 md:grid-cols-2 lg:grid-cols-4 lg:gap-12">
              <div className="flex flex-col items-center space-y-2 rounded-lg border p-6 shadow-sm">
                <div className="rounded-full bg-blue-900 p-3">
                  <FileAudio className="h-6 w-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold">Audio Files</h3>
                <p className="text-center text-muted-foreground">
                  Organize music and audio files by artist, album, genre, and
                  more.
                </p>
              </div>
              <div className="flex flex-col items-center space-y-2 rounded-lg border p-6 shadow-sm">
                <div className="rounded-full bg-blue-900 p-3">
                  <FileVideo className="h-6 w-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold">Video Files</h3>
                <p className="text-center text-muted-foreground">
                  Sort videos by title, director, year, resolution, and other
                  metadata.
                </p>
              </div>
              <div className="flex flex-col items-center space-y-2 rounded-lg border p-6 shadow-sm">
                <div className="rounded-full bg-blue-900 p-3">
                  <FileImage className="h-6 w-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold">Image Files</h3>
                <p className="text-center text-muted-foreground">
                  Categorize images by date, camera model, location, and more.
                </p>
              </div>
              <div className="flex flex-col items-center space-y-2 rounded-lg border p-6 shadow-sm">
                <div className="rounded-full bg-blue-900 p-3">
                  <BookOpen className="h-6 w-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold">Ebooks</h3>
                <p className="text-center text-muted-foreground">
                  Organize ebooks by author, title, genre, publisher, and more.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section
          id="how-it-works"
          className="w-full py-12 md:py-24 lg:py-32 bg-blue-950"
        >
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <div className="inline-block rounded-lg bg-blue-900 px-3 py-1 text-sm text-blue-300">
                  How It Works
                </div>
                <h2 className="text-3xl font-bold tracking-tighter md:text-4xl/tight">
                  Simple Yet Powerful
                </h2>
                <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Archimedius makes organizing your media files straightforward
                  with a few simple steps.
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl gap-6 py-12 md:grid-cols-1 lg:gap-12">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <div className="flex flex-col items-center space-y-2 rounded-lg border bg-background p-6 shadow-sm">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-900 text-xl font-bold text-blue-400">
                    1
                  </div>
                  <h3 className="text-xl font-bold">Select Directories</h3>
                  <p className="text-center text-muted-foreground">
                    Choose your source and destination directories for media
                    files.
                  </p>
                </div>
                <div className="flex flex-col items-center space-y-2 rounded-lg border bg-background p-6 shadow-sm">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-900 text-xl font-bold text-blue-400">
                    2
                  </div>
                  <h3 className="text-xl font-bold">Configure Templates</h3>
                  <p className="text-center text-muted-foreground">
                    Set up organization templates for each media type.
                  </p>
                </div>
                <div className="flex flex-col items-center space-y-2 rounded-lg border bg-background p-6 shadow-sm">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-900 text-xl font-bold text-blue-400">
                    3
                  </div>
                  <h3 className="text-xl font-bold">Select File Types</h3>
                  <p className="text-center text-muted-foreground">
                    Choose which media types to process (audio, video, images,
                    ebooks).
                  </p>
                </div>
                <div className="flex flex-col items-center space-y-2 rounded-lg border bg-background p-6 shadow-sm">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-900 text-xl font-bold text-blue-400">
                    4
                  </div>
                  <h3 className="text-xl font-bold">Organize</h3>
                  <p className="text-center text-muted-foreground">
                    Let Archimedius extract metadata and organize your files.
                  </p>
                </div>
              </div>
              <div className="rounded-lg border bg-background p-6 shadow-sm">
                <h3 className="text-xl font-bold mb-4">Example Template</h3>
                <div className="bg-muted p-4 rounded-md font-mono text-sm overflow-x-auto">
                  <p className="text-blue-400">Audio Template:</p>
                  <p>
                    Music/{"{artist}"}/{"{album}"}/
                    {"{track_number:02d} - {title}"}
                  </p>
                  <p className="mt-2 text-blue-400">Video Template:</p>
                  <p>
                    Videos/{"{year}"}/{"{title}"}
                  </p>
                  <p className="mt-2 text-blue-400">Image Template:</p>
                  <p>
                    Photos/{"{year}"}/{"{month}"}/{"{day}"}/{"{filename}"}
                  </p>
                  <p className="mt-2 text-blue-400">Ebook Template:</p>
                  <p>
                    Books/{"{author}"}/{"{title}"}
                  </p>
                </div>
              </div>
              <div className="flex justify-center">
                <Image
                  src="/screenshot.png"
                  width={800}
                  height={640}
                  alt="Archimedius Application Interface"
                  className="rounded-lg shadow-xl border border-muted"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Download Section */}
        <section id="download" className="w-full py-12 md:py-24 lg:py-32">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter md:text-4xl/tight">
                  Ready to Organize Your Media Collection?
                </h2>
                <p className="max-w-[600px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Download Archimedius today and start organizing your media
                  files with intelligent metadata extraction.
                </p>
              </div>
              <div className="flex flex-col gap-2 min-[400px]:flex-row">
                <Button
                  className="inline-flex h-10 items-center justify-center bg-blue-600 hover:bg-blue-700"
                  size="lg"
                >
                  Download for Windows
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  className="inline-flex h-10 items-center justify-center"
                  size="lg"
                >
                  Download for macOS
                </Button>
                <Button
                  variant="outline"
                  className="inline-flex h-10 items-center justify-center"
                  size="lg"
                >
                  Download for Linux
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Version 1.0.0 | Python 3.6+ required
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full border-t bg-background py-6 md:py-12">
        <div className="container px-4 md:px-6">
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Image
                  src="/logo.png"
                  alt="Archimedius Logo"
                  width={24}
                  height={24}
                  className="rounded"
                />
                <span className="text-xl font-bold">Archimedius</span>
              </div>
              <p className="text-sm text-muted-foreground">
                A cross-platform desktop application for organizing media files
                based on metadata.
              </p>
              <div className="flex space-x-4">
                <Link
                  href="#"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <Twitter className="h-5 w-5" />
                  <span className="sr-only">Twitter</span>
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <Github className="h-5 w-5" />
                  <span className="sr-only">GitHub</span>
                </Link>
              </div>
            </div>
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Product</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link
                    href="#features"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Features
                  </Link>
                </li>
                <li>
                  <Link
                    href="#download"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Download
                  </Link>
                </li>
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Changelog
                  </Link>
                </li>
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Roadmap
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Resources</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Tutorials
                  </Link>
                </li>
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    GitHub Repository
                  </Link>
                </li>
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Issue Tracker
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Legal</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link
                    href="#"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    License
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-8 border-t pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} Archimedius. All rights
              reserved.
            </p>
            <p className="text-xs text-muted-foreground mt-4 md:mt-0">
              Built with Python and Tkinter. Logo design by Archimedius Team.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
