#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );
use v5.10;

use cPanelUserConfig;
use Path::Tiny qw/path/;
use Prism;
use DBI;
use JSON::MaybeXS;
use Digest::SHA qw/sha256_hex/;
use Storable qw/dclone/; 

# =================
# = PREPROCESSING =
# =================

my $prism = Prism->new( file => ($ARGV[0] eq 'seed') ? 'seed.yml' : 'update.yml', agent => 'Auditor (io.canada.ca:v1.2)' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1, AutoCommit => 1, RaiseError => 0 }
);

my $coder = JSON::MaybeXS->new( utf8 => 1 );

my $add = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'create'} );

while (my $resource = $prism->next() )
{
    
    my $io = $coder->decode( $prism->get( $resource->{'uri'} )->{'content'} );
    
    foreach my $recall (  @{ $io->{'results'} }  )
    {
        my $predata = $prism->overlay( $recall, dclone( $resource ) );
                
        my ( $url, $lang ) = map { $predata->{ $_ } } ('source', 'lang') ;
        
        my  $uid = generateUID( $url, $lang );

        if ( $dbh->selectrow_array( $prism->config->{'database'}->{'sql'}->{'read'}, undef, $uid, $lang ) )
		{
			say " [skipping] duplicate $url";
			next;
		}
        
        # lets make sure we do not throttle the service
        sleep( 1 );        
        
        my $data = $coder->decode( $prism->get( $url )->{'content'} );
        
        # lets set the category and sub category
        my $section = $data->{'panels'}->[0]->{'text'};

        $data->{'abstract'} = $data->{'panels'}->[1]->{'text'};

        my @secs = ( $section =~ m/<b>(Catégorie|Category):<\/b>(.*?)<BR\/>/ );

        my $rez = dclone( $resource );
        
        my $dataset = $prism->transform( $data, $rez );
		
		# lets remap the id since this based on the asking URL
		$dataset->{'id'} = $uid ;
        
        # lets make sure we have a title
        unless ( $dataset->{'title'} ||  $dataset->{'title'} ne '' )
        {
            say " [skipping] empty recordet $url";
            next;
        }

        my $categories = categorize ( pop @secs );

        # lets clear out the keys
        $dataset->{'category'} = $dataset->{'subcategory'} = "";

        foreach my $indx ( keys $categories )
        {
            $dataset->{ 'category' } = append( $dataset->{ 'category' }, $indx );
            if ( scalar @{ $categories->{$indx} } )
            {
                $dataset->{ 'subcategory' } =  append( $dataset->{ 'subcategory' }, $_ )  for ( @{ $categories->{$indx} }  );
            }
        }
        
        $add->execute( map { $dataset->{$_} }  split ' ', $prism->config->{'database'}->{'sql'}->{'fields'} );
        print " [added] ".$url."\n";
    }

}


sub normalize
{
    my ( $text ) = @_;

    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    
    return $text;
}

sub canonalize
{
    my ( $url ) = @_;
    $url =~ s/(http[s]*\:\/\/)www\./$1/;
    return $url;
}

sub generateUID
{
    my ( $url, $lang ) = @_;
    my ( $uid ) = $url =~ m/(^.*)\/$lang$/;
    
    return sha256_hex( $uid );
}

sub categorize
{
    my ( $catalog, $text ) = ( {}, @_ ) ;

    foreach my $entry ( split /,\s*/, normalize( $text ) )
    {
        my ( $category, $sub ) = split /\s*-\s*/, $entry;
        # lets create a child category
        $catalog->{ $category } = [] unless ( $catalog->{ $category } );
        push @{ $catalog->{ $category } }, $sub if ( $sub );
    }
    return $catalog;
}

sub append
{
    my ( $base, $addition ) = @_;
    return $addition unless ( $base =~ m/\S/ );
    return ( $base =~ m/\b\Q$addition\E\b/ ) ? $base : $base.", ".$addition;
}
      
