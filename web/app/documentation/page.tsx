import Link from "next/link"
import Image from "next/image"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BookOpen,
  FileAudio,
  FileImage,
  FileVideo,
  HelpCircle,
  Info,
  LayoutTemplate,
  Lightbulb,
  Wrench,
} from "lucide-react"

export default function DocumentationPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Image
              src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Icon1024-NQrw6m9CO32rrXYKQfBvmYVmjqBErs.png"
              alt="Archimedius Logo"
              width={32}
              height={32}
              className="rounded"
            />
            <span className="text-xl font-bold">Archimedius</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/" className="text-sm font-medium hover:text-primary">
              Home
            </Link>
            <Link href="/documentation" className="text-sm font-medium text-primary">
              Documentation
            </Link>
            <Link href="/download" className="text-sm font-medium hover:text-primary">
              Download
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1 container py-8">
        <div className="flex flex-col space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">Documentation</h1>
            <p className="text-muted-foreground">Comprehensive documentation for the Archimedius application.</p>
          </div>

          <Tabs defaultValue="getting-started" className="w-full">
            <TabsList className="grid w-full grid-cols-2 md:grid-cols-5">
              <TabsTrigger value="getting-started" className="flex items-center gap-2">
                <Info className="h-4 w-4" />
                <span className="hidden md:inline">Getting Started</span>
              </TabsTrigger>
              <TabsTrigger value="templates" className="flex items-center gap-2">
                <LayoutTemplate className="h-4 w-4" />
                <span className="hidden md:inline">Templates</span>
              </TabsTrigger>
              <TabsTrigger value="file-types" className="flex items-center gap-2">
                <FileAudio className="h-4 w-4" />
                <span className="hidden md:inline">File Types</span>
              </TabsTrigger>
              <TabsTrigger value="tips" className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4" />
                <span className="hidden md:inline">Tips & Tricks</span>
              </TabsTrigger>
              <TabsTrigger value="troubleshooting" className="flex items-center gap-2">
                <Wrench className="h-4 w-4" />
                <span className="hidden md:inline">Troubleshooting</span>
              </TabsTrigger>
            </TabsList>

            {/* Getting Started Tab */}
            <TabsContent value="getting-started" className="space-y-6 mt-6">
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Getting Started with Archimedius</h2>
                <p className="text-muted-foreground">
                  Archimedius helps you organize your media files (audio, video, images, and eBooks) based on their
                  metadata. This guide will help you get started with the basic features.
                </p>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Basic Steps</CardTitle>
                  <CardDescription>Follow these steps to organize your media files</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="font-semibold">1. Select Source Directory</h3>
                    <p className="text-sm text-muted-foreground">
                      Click the 'Browse...' button next to 'Source Directory' to select the folder containing your media
                      files.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">2. Select Output Directory</h3>
                    <p className="text-sm text-muted-foreground">
                      Click the 'Browse...' button next to 'Output Directory' to select where you want your organized
                      files to be placed.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">3. Choose File Types</h3>
                    <p className="text-sm text-muted-foreground">
                      Select which types of media files you want to organize by checking the appropriate boxes in the
                      'File Type Filters' section.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">4. Configure Templates</h3>
                    <p className="text-sm text-muted-foreground">
                      Set up organization templates for each media type using the tabs in the 'Organization Templates'
                      section.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">5. Generate Preview</h3>
                    <p className="text-sm text-muted-foreground">
                      Click the 'Analyze' button to see a preview of how your files will be organized.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">6. Start Organization</h3>
                    <p className="text-sm text-muted-foreground">
                      Click 'Copy All' to copy files to the new structure, or 'Move All' to move them.
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Interface Overview</CardTitle>
                  <CardDescription>Understanding the Archimedius interface</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="font-semibold">Source and Output Directories</h3>
                    <p className="text-sm text-muted-foreground">
                      At the top of the window, you can select the source directory (where your files are located) and
                      the output directory (where organized files will be placed).
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">File Type Filters</h3>
                    <p className="text-sm text-muted-foreground">
                      This section allows you to select which types of files to include in the organization process. You
                      can select all files of a type or individual extensions.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">Organization Templates</h3>
                    <p className="text-sm text-muted-foreground">
                      This section lets you define how files should be organized using placeholders for metadata.
                      Different tabs allow you to set templates for each media type.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">Preview</h3>
                    <p className="text-sm text-muted-foreground">
                      The central area shows a preview of how your files will be organized, with source and destination
                      paths.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">Progress</h3>
                    <p className="text-sm text-muted-foreground">
                      The bottom section shows progress information during the organization process.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Templates Tab */}
            <TabsContent value="templates" className="space-y-6 mt-6">
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Organization Templates</h2>
                <p className="text-muted-foreground">
                  Templates determine how your files will be organized. They use placeholders (enclosed in curly braces)
                  that will be replaced with actual metadata from your files. For example,{" "}
                  {"{artist}/{album}/{filename}"}
                  would organize music files by artist, then by album.
                </p>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Common Placeholders</CardTitle>
                  <CardDescription>Placeholders available for all file types</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{filename}"}</div>
                      <div className="text-sm">Original filename without extension</div>
                    </div>
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{extension}"}</div>
                      <div className="text-sm">File extension (e.g., mp3, jpg)</div>
                    </div>
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{file_type}"}</div>
                      <div className="text-sm">Type of file (audio, video, image, ebook)</div>
                    </div>
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{size}"}</div>
                      <div className="text-sm">File size in bytes</div>
                    </div>
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{creation_date}"}</div>
                      <div className="text-sm">File creation date (YYYY-MM-DD)</div>
                    </div>
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{creation_year}"}</div>
                      <div className="text-sm">Year of file creation (YYYY)</div>
                    </div>
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{creation_month}"}</div>
                      <div className="text-sm">Month of file creation (01-12)</div>
                    </div>
                    <div className="flex items-start">
                      <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{creation_month_name}"}</div>
                      <div className="text-sm">Month name of file creation</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <FileAudio className="h-5 w-5 text-blue-500" />
                    <div>
                      <CardTitle>Audio Placeholders</CardTitle>
                      <CardDescription>For music and audio files</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{title}"}</div>
                        <div className="text-sm">Song title</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{artist}"}</div>
                        <div className="text-sm">Artist name</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{album}"}</div>
                        <div className="text-sm">Album name</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{year}"}</div>
                        <div className="text-sm">Release year</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{genre}"}</div>
                        <div className="text-sm">Music genre</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{track}"}</div>
                        <div className="text-sm">Track number</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{duration}"}</div>
                        <div className="text-sm">Song duration</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{bitrate}"}</div>
                        <div className="text-sm">Audio bitrate</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <FileImage className="h-5 w-5 text-green-500" />
                    <div>
                      <CardTitle>Image Placeholders</CardTitle>
                      <CardDescription>For photos and images</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{width}"}</div>
                        <div className="text-sm">Image width in pixels</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{height}"}</div>
                        <div className="text-sm">Image height in pixels</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{format}"}</div>
                        <div className="text-sm">Image format (e.g., JPEG, PNG)</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{camera_make}"}</div>
                        <div className="text-sm">Camera manufacturer</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{camera_model}"}</div>
                        <div className="text-sm">Camera model</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{date_taken}"}</div>
                        <div className="text-sm">Date when the photo was taken</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <BookOpen className="h-5 w-5 text-amber-500" />
                    <div>
                      <CardTitle>eBook Placeholders</CardTitle>
                      <CardDescription>For digital books</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{title}"}</div>
                        <div className="text-sm">Book title</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{author}"}</div>
                        <div className="text-sm">Author name</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{year}"}</div>
                        <div className="text-sm">Publication year</div>
                      </div>
                      <div className="flex items-start">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm mr-2">{"{genre}"}</div>
                        <div className="text-sm">Book genre</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Example Templates</CardTitle>
                    <CardDescription>Common organization patterns</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="space-y-1">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm">
                          {"{file_type}/{artist}/{album}/{filename}"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Organizes by file type, then artist, then album
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm">
                          {"Music/{year}/{artist} - {title}.{extension}"}
                        </div>
                        <div className="text-sm text-muted-foreground">Organizes music by year, then artist-title</div>
                      </div>
                      <div className="space-y-1">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm">
                          {"{file_type}/{creation_year}/{creation_month_name}/{filename}"}
                        </div>
                        <div className="text-sm text-muted-foreground">Organizes by file type, year, and month</div>
                      </div>
                      <div className="space-y-1">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm">
                          {"Photos/{creation_year}/{creation_month}/{filename}"}
                        </div>
                        <div className="text-sm text-muted-foreground">Organizes photos by year and month number</div>
                      </div>
                      <div className="space-y-1">
                        <div className="font-mono bg-muted px-2 py-1 rounded text-sm">
                          {"{author}/{title}/{filename}"}
                        </div>
                        <div className="text-sm text-muted-foreground">Organizes eBooks by author and title</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* File Types Tab */}
            <TabsContent value="file-types" className="space-y-6 mt-6">
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Supported File Types</h2>
                <p className="text-muted-foreground">
                  Archimedius supports various file types across different media categories. You can select which file
                  types to include in the organization process using the checkboxes in the 'File Type Filters' section.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <FileAudio className="h-5 w-5 text-blue-500" />
                    <div>
                      <CardTitle>Audio Files</CardTitle>
                      <CardDescription>Music and sound recordings</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      Audio files contain music or other sound recordings. The application can extract metadata such as
                      artist, album, title, and genre.
                    </p>
                    <div className="bg-muted rounded p-2">
                      <p className="text-sm font-medium">Supported formats:</p>
                      <p className="text-sm">MP3, FLAC, M4A, AAC, OGG, WAV</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <FileVideo className="h-5 w-5 text-red-500" />
                    <div>
                      <CardTitle>Video Files</CardTitle>
                      <CardDescription>Movies and video recordings</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      Video files contain moving images and usually audio. The application can extract metadata such as
                      title, duration, and creation date.
                    </p>
                    <div className="bg-muted rounded p-2">
                      <p className="text-sm font-medium">Supported formats:</p>
                      <p className="text-sm">MP4, MKV, AVI, MOV, WMV</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <FileImage className="h-5 w-5 text-green-500" />
                    <div>
                      <CardTitle>Image Files</CardTitle>
                      <CardDescription>Photos and pictures</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      Image files contain still pictures. The application can extract metadata such as dimensions,
                      camera information, and date taken.
                    </p>
                    <div className="bg-muted rounded p-2">
                      <p className="text-sm font-medium">Supported formats:</p>
                      <p className="text-sm">JPG/JPEG, PNG, GIF, BMP, TIFF</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <BookOpen className="h-5 w-5 text-amber-500" />
                    <div>
                      <CardTitle>eBook Files</CardTitle>
                      <CardDescription>Digital books</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      eBook files contain digital books. The application can extract metadata such as title, author, and
                      publication date.
                    </p>
                    <div className="bg-muted rounded p-2">
                      <p className="text-sm font-medium">Supported formats:</p>
                      <p className="text-sm">PDF, EPUB, MOBI, AZW</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Tips & Tricks Tab */}
            <TabsContent value="tips" className="space-y-6 mt-6">
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Tips & Tricks</h2>
                <p className="text-muted-foreground">Here are some helpful tips to get the most out of Archimedius.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Preview Before Organizing
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Always use the 'Analyze' button to preview how your files will be organized before starting the
                      actual organization process.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Backup Your Files
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      When first using the application, use the 'Copy All' option instead of 'Move All' to ensure your
                      original files remain intact until you're confident with the results.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Customize Templates
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Different media types have different metadata. Use the tabs in the 'Organization Templates'
                      section to set appropriate templates for each type.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Use the Placeholders Help
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Click the 'Placeholders Help' button in the templates section to see all available placeholders
                      and examples.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Save Your Settings
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Your settings are automatically saved, but you can manually save them using Settings > Save
                      Settings if you've made changes you want to keep.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Check the Logs
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      If something doesn't work as expected, check the logs (View > Show Logs) for more detailed
                      information about what happened.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Organize by Date
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      For photos and videos, organizing by creation date (e.g.,{" "}
                      {"{creation_year}/{creation_month_name}"}) is often a good approach.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Organize Music by Metadata
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      For music files, organizing by artist and album (e.g., {"{artist}/{album}"}) helps keep your
                      collection well-structured.
                    </p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Troubleshooting Tab */}
            <TabsContent value="troubleshooting" className="space-y-6 mt-6">
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Troubleshooting</h2>
                <p className="text-muted-foreground">
                  If you encounter issues while using Archimedius, here are solutions to some common problems.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      No Files Found
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      If no files are found in the source directory, check that you've selected the correct directory
                      and that you've enabled the appropriate file types in the 'File Type Filters' section.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      Missing Metadata
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      If metadata is missing (shown as 'Unknown' in the organized path), the file may not contain that
                      metadata. Try using different placeholders in your template.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      Organization Process is Slow
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Processing large numbers of files, especially video files, can take time. Be patient, and check
                      the progress indicator at the bottom of the window.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      Application Freezes
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      If the application appears to freeze during organization, it may be processing a large file. Check
                      the logs (View > Show Logs) for more information.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      Destination Path Already Exists
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      If a file with the same name already exists at the destination, the application will append a
                      number to the filename to avoid overwriting.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      Permission Errors
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      If you encounter permission errors, make sure you have the necessary permissions to read from the
                      source directory and write to the output directory.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      Metadata Not Extracted Correctly
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Some files may have incomplete or incorrect metadata. You can use tools like MP3Tag (for audio) or
                      ExifTool (for images) to fix the metadata before organizing.
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-red-500" />
                      Templates Not Working
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Make sure your templates use valid placeholders enclosed in curly braces {}. Check the 'Templates'
                      tab in this help dialog for a list of valid placeholders.
                    </p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>

      <footer className="w-full border-t bg-background py-6 md:py-12">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2">
              <Image
                src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Icon1024-NQrw6m9CO32rrXYKQfBvmYVmjqBErs.png"
                alt="Archimedius Logo"
                width={24}
                height={24}
                className="rounded"
              />
              <span className="text-xl font-bold">Archimedius</span>
            </div>
            <p className="text-sm text-muted-foreground mt-4 md:mt-0">
              &copy; {new Date().getFullYear()} Archimedius. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

