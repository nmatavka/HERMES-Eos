package OpenSSL::safe::installdata;

use strict;
use warnings;
use Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw(
    @PREFIX
    @libdir
    @BINDIR @BINDIR_REL_PREFIX
    @LIBDIR @LIBDIR_REL_PREFIX
    @INCLUDEDIR @INCLUDEDIR_REL_PREFIX
    @APPLINKDIR @APPLINKDIR_REL_PREFIX
    @ENGINESDIR @ENGINESDIR_REL_LIBDIR
    @MODULESDIR @MODULESDIR_REL_LIBDIR
    @PKGCONFIGDIR @PKGCONFIGDIR_REL_LIBDIR
    @CMAKECONFIGDIR @CMAKECONFIGDIR_REL_LIBDIR
    $VERSION @LDLIBS
);

our @PREFIX                     = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install' );
our @libdir                     = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/lib' );
our @BINDIR                     = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/bin' );
our @BINDIR_REL_PREFIX          = ( 'bin' );
our @LIBDIR                     = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/lib' );
our @LIBDIR_REL_PREFIX          = ( 'lib' );
our @INCLUDEDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/include' );
our @INCLUDEDIR_REL_PREFIX      = ( 'include' );
our @APPLINKDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/include/openssl' );
our @APPLINKDIR_REL_PREFIX      = ( 'include/openssl' );
our @ENGINESDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/lib/engines-3' );
our @ENGINESDIR_REL_LIBDIR      = ( 'engines-3' );
our @MODULESDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/lib/ossl-modules' );
our @MODULESDIR_REL_LIBDIR      = ( 'ossl-modules' );
our @PKGCONFIGDIR               = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/lib/pkgconfig' );
our @PKGCONFIGDIR_REL_LIBDIR    = ( 'pkgconfig' );
our @CMAKECONFIGDIR             = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/install/lib/cmake/OpenSSL' );
our @CMAKECONFIGDIR_REL_LIBDIR  = ( 'cmake/OpenSSL' );
our $VERSION                    = '3.5.5';
our @LDLIBS                     =
    # Unix and Windows use space separation, VMS uses comma separation
    $^O eq 'VMS'
    ? split(/ *, */, ' ')
    : split(/ +/, ' ');

1;
