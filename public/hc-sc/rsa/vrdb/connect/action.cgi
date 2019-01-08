#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );
use v5.10;

use cPanelUserConfig;
use Storable qw/dclone/; 
use Path::Tiny qw/path/;

use Prism;
use DBI;
use YAML::Tiny;
use Text::CSV_XS;
use DateTime;
use Digest::SHA qw/sha256_hex/;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => ($ARGV[0] eq 'seed') ? 'seed.yml' : 'update.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1, AutoCommit => 1, RaiseError => 0 }
);

my $add = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'create'} );
my $update = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'update'} );
my ( $latest ) = $dbh->selectrow_array( $prism->config->{'database'}->{'sql'}->{'latest'} );


while ( my $resource = $prism->next() )
{    
    my $io = $prism->download( $resource->{'uri'}, $resource->{'source'} );
    
    if ( $io == undef )
    {
        $io = $prism->basedir->child( $resource->{'source'} );
    }
        
    $io = $io->openr;
	    
    my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                    or die "Cannot use CSV: ".Text::CSV->error_diag ();
                    
    $csv->column_names( @{ $csv->getline( $io ) } );
    
    while (my $row = $csv->getline_hr( $io ) )
    {
        my $rez = dclone( $resource );
		
        my $dataset = $prism->transform( $row, $rez );
        
		if ( $ARGV[0] ne 'seed' && $latest > $dataset->{'date'} )
		{
			say "	[skipping] already indexed ".$dataset->{'url'};
			next;
		}
		
        $dataset = normalize( $dataset );
		
		$dataset->{'id'} = getUID( $dataset->{'url'} );
        
        # lets check if this recall exists
        if ( my ( $id, $sub, $title, $lang, $year ) = $dbh->selectrow_array( $prism->config->{'database'}->{'sql'}->{'read'}, {}, $dataset->{'id'}, $dataset->{'lang'} ))
		{
			
            if ( contains( $dataset->{'subcategory'}, $sub ) && contains( $dataset->{'year'}, $year )  )
            {
				say "	[skipping] duplicate ".$dataset->{'url'};
				next;
            }
            
		    say "	[merging] ".$dataset->{'url'};
			merge( $dataset , $id, $sub, $title, $lang, $year );
			
			next;
        }
        
        $add->execute( map { $dataset->{$_} }  split ' ', $prism->config->{'database'}->{'sql'}->{'fields'} );
        
        say "	[added] ".$dataset->{'url'};
        
    }
        
}

# Functions
#########################################
sub normalize
{
    my ( $dataset ) = @_ ;
    
    my $normalized = {};
    
    foreach my $entry ( keys $dataset )
    {
        $normalized->{ $entry } = ( $dataset->{ $entry } eq 'Not Entered' || $dataset->{ $entry } eq 'Non Saisie')
                                        ? '' : $dataset->{ $entry };
    }
    
    return $normalized;
}

sub getUID
{
	my ( $url ) = @_;
	$url =~ s/lang=(fra|eng)\&rn=/rn=/;
	return sha256_hex( $url );
}

sub isLatest
{
	my ( $date ) = @_;
	say " [latest] ".$latest.' :: '.$date;
	
	return $latest == $date ;
}

sub contains
{
	my ($needle, $haystack ) = @_;
	
	#say " [needle]:$needle / [haystack]:$haystack";
	
	if ( $haystack =~ m/(^|\s)\Q$needle\E[,]/ )
	{
		return 1;
	}
	
	if ( $haystack =~ m/(^|\s)\Q$needle\E$/ )
	{
		return 1;
	}
	
	return 0;
}

sub merge
{
	my ( $dataset, $id, $sub, $title, $lang, $year ) = @_;
	
    $title .= ', ' . $dataset->{'subcategory'} unless contains( $dataset->{'subcategory'}, $title );
    $sub .= ', ' . $dataset->{'subcategory'} unless contains( $dataset->{'subcategory'}, $sub );
    $year .= ', ' . $dataset->{'year'} unless contains( $dataset->{'year'}, $year );
	
    $update->execute( $title, $sub, $year , $id, $lang );
}
