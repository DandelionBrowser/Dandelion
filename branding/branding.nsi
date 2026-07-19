# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# NSIS branding defines for the Dandelion Windows installer.

# BrandFullNameInternal is used for some registry and file system values
# instead of BrandFullName and typically should not be modified.
!define BrandFullNameInternal "Dandelion"
!define BrandFullName         "Dandelion"
!define CompanyName           "Dandelion"
!define URLInfoAbout          "https://github.com/DandelionBrowser/Dandelion"
!define HelpLink              "https://github.com/DandelionBrowser/Dandelion/issues"

# Dandelion has no stub installer and no download server, so the manual
# download link points at the release listing for every architecture.
!define URLStubDownloadX86 "https://github.com/DandelionBrowser/Dandelion/releases"
!define URLStubDownloadAMD64 "https://github.com/DandelionBrowser/Dandelion/releases"
!define URLStubDownloadAArch64 "https://github.com/DandelionBrowser/Dandelion/releases"
!define URLManualDownload "https://github.com/DandelionBrowser/Dandelion/releases"

!define Channel "release"
