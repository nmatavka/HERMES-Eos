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

our @PREFIX                     = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src' );
our @libdir                     = ( '' );
our @BINDIR                     = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src/apps' );
our @BINDIR_REL_PREFIX          = ( 'apps' );
our @LIBDIR                     = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src' );
our @LIBDIR_REL_PREFIX          = ( '' );
our @INCLUDEDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src/include', '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src/include' );
our @INCLUDEDIR_REL_PREFIX      = ( 'include', './include' );
our @APPLINKDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src/ms' );
our @APPLINKDIR_REL_PREFIX      = ( 'ms' );
our @ENGINESDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src/engines' );
our @ENGINESDIR_REL_LIBDIR      = ( 'engines' );
our @MODULESDIR                 = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src/providers' );
our @MODULESDIR_REL_LIBDIR      = ( 'providers' );
our @PKGCONFIGDIR               = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src' );
our @PKGCONFIGDIR_REL_LIBDIR    = ( '.' );
our @CMAKECONFIGDIR             = ( '/Users/nick/eudora-carbon/XcodeSupport/Generated/OpenSSL/darwin-i386/work/src' );
our @CMAKECONFIGDIR_REL_LIBDIR  = ( '.' );
our $VERSION                    = '3.5.5';
our @LDLIBS                     =
    # Unix and Windows use space separation, VMS uses comma separation
    $^O eq 'VMS'
    ? split(/ *, */, ' ')
    : split(/ +/, ' ');

1;
