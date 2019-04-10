#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );
use v5.10;

use cPanelUserConfig;

use Prism;
use YAML::Tiny;
use Path::Tiny qw/path/;
use Text::CSV_XS;
use JSON::XS;
use Archive::Zip;
use HTML::Entities;

use Time::Piece;
use Text::Markdown 'markdown';
use Text::StripAccents;

# =================
# = PREPROCESSING =
# =================
my $datadir = path($0)->parent(2);
my $prism = Prism->new( file => 'action.yml' );
my $config = $prism->config;
my $coder = JSON::XS->new->utf8;

my $now = localtime;
my $scnds = $now->epoch; 

my ( $rolodex, $departments, $status ) = (
    $config->{'subjects'},
    $config->{'departments'},
    $config->{'status'}
);

my $update = 0;

while ( my $resource = $prism->next() )
{
    my $lang = $resource->{'lang'};

    my $io = $prism->download( $resource->{'uri'}, $resource->{'source'} );
    
    unless ( $io  )
    {
        say '   [skipping] '.$resource->{'uri'}.' not modified';
        next;
    };

    $update = 1;

    $io = $io->openr;

    my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
        or die "Cannot use CSV: ".Text::CSV->error_diag ();

    $csv->column_names( @{ $csv->getline( $io ) } );

    my $indx = { 'data' => [] };

    while (my $row = $csv->getline_hr( $io ) )
    {

        my $dataset = {
            start_date => { text => dateformat( $row->{'start_date'}, $lang ), iso => $row->{'start_date'}, epoch => epoch( $row->{'start_date'} ) },
            end_date => { text => dateformat( $row->{'end_date'}, $lang ), iso => $row->{'end_date'}, epoch => epoch( $row->{'end_date'} ) },
            status => { text => extroplate( $row->{'status'}, $lang, $status ), order => extroplate( $row->{'status'}, 'order', $status ), label => extroplate( $row->{'status'}, 'label', $status )  },
            subject =>  extroplate( $row->{'subjects'}, $lang, $rolodex ),
            title => ( $lang eq 'en' )  ? $row->{'title_en'} : $row->{'title_fr'},
            description => ( $lang eq 'en' )  ? $row->{'description_en'} : $row->{'description_fr'},
            owner => splitselect( '\s+\|\s+', $row->{'owner_org_title'}, $lang )
        };
          
        # lets see if we have a profile page
        
        if ( begins_with( $row->{'profile_page_en'}, 'http' ) )
        {
            $dataset->{'link'} = ( $lang eq 'en' )  ? $row->{'profile_page_en'} : $row->{'profile_page_fr'};
        }

        push( @{ $indx->{'data'} }, $dataset );
    }
    
    # lets sort by end date
    
    $indx->{'data'} = [ sort { $a->{'status'}->{'order'} <=> $b->{'status'}->{'order'} || $a->{'end_date'}->{'epoch'} <=> $b->{'end_date'}->{'epoch'} } @{ $indx->{'data'} } ];
      
    $indx->{'total'} = scalar( @{ $indx->{'data'} } );
    
    $datadir->child( $lang, 'index.json')->touchpath->spew_raw( $coder->encode( $indx  ) );

}


if ( $update )
{

    my $zip = Archive::Zip->new();

    $zip->addTree( $datadir->child( $_ )->absolute->realpath->stringify, $_ ) for ('en', 'fr');

    $zip->overwriteAs({ filename => $datadir->child('all.zip')->absolute->realpath->stringify });
}



# ----------------------------------------------------------------------------------------------
# Functions
# ..............................................................................................
sub extroplate
{
    my ($text, $lang, $dictionary ) = @_;
    my @subjects = split( /,/, $text );
    for ( my $idx = 0; $idx < scalar(@subjects); $idx++ )
    {
        $subjects[$idx] = $dictionary->{ $subjects[$idx] }->{$lang};
    }
    return join( ' | ', @subjects );
}


sub toiso
{
    my @date = split( /\//, shift );
    return sprintf "%04d-%02d-%02d", reverse @date;
}

sub splitselect
{
    my ($sep, $text, $lang ) = @_;
    my @choices = split( /$sep/, $text );
    return ( $lang eq 'en' ) ? $choices[0] : $choices[1];
}

sub normalize
{
    my ( $text ) = @_;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    return $text;
}

sub compress
{
    my ( $text ) = @_;
    $text =~ s/\R//g;
    $text =~ s/\s+/ /g;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    return $text;
}

sub begins_with
{
    return substr($_[0], 0, length($_[1])) eq $_[1];
}

sub sanitize
{
    my ( $text ) = @_;
    $text =~ s/\n+//g;
    $text =~ s/\s+/_/g;
    return $text;
}

sub generate
{
    my ( $text ) = @_;
    $text = stripaccents($text);
    $text =~ s/[^a-z]//gi;
    return lc($text);
}

sub dateformat
{
    my ($dstr, $lang) = @_;
    my $tmsp = Time::Piece->strptime($dstr, '%Y-%m-%d');
    return ($lang eq 'en')
        ? $tmsp->month( @{ $config->{'dates'}->{'months'}->{'en'} } )." ".$tmsp->mday.", ".$tmsp->year
        : $tmsp->mday." ".$tmsp->month( @{ $config->{'dates'}->{'months'}->{'fr'} } )." ".$tmsp->year;
}


sub epoch
{
    my ( $dstr ) = @_;
    my $tmsp = Time::Piece->strptime($dstr, '%Y-%m-%d');
    my $epch = $tmsp->epoch;
    
    return ( $epch > $scnds ) ? $epch - $scnds : $scnds + ( $scnds - $epch ) ;
    
}

