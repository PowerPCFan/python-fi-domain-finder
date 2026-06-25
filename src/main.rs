use prompted::input;
use reqwest::Client;
use tokio::{main};
use futures::stream::{self, StreamExt};

mod wordprocessor;
mod availabilitycheck;

#[main]
async fn main() {
    let path = input!("Enter the file path for a list of words (seperated by newlines): ");
    let mut tld = input!("Enter your desired TLD (e.g .fi): ");

    if !tld.starts_with("."){
        tld = ".".to_owned() + &tld;
    }

    let word_length = input!("Amount of letters for the domain? (Excluding TLD. e.g google.com would be 6. enter 0 for any): ");

    let word_length: usize = match word_length.trim().parse() {
        Ok(num) => num,
        Err(_) => panic!("Invalid word length!")
    };
    
    
    let max_conns = input!("How many requests can be active at a time? (defualt 5): ");
        
    let max_connections: usize = match max_conns.trim().parse() {
        Ok(num) => num,
        Err(_) => panic!("Invalid maximum connections!")
    };

    let raw_words = wordprocessor::load_words(&path);
    let words = wordprocessor::find_n_letter_words(raw_words.clone(), word_length);
    
    println!("Words that fit the word length: {} (out of {})", words.len(), raw_words.len());
    println!("Starting checking for domains...");

    stream::iter(words)
        .map(|word| {
            let client = Client::new();
            let tld = tld.clone();
            async move {
                availabilitycheck::check_domain_available(&client, &format!("{}{}", word.replace("-","").trim(), tld.trim())).await;
            }
        })
        .buffer_unordered(max_connections)
        .collect::<Vec<_>>()
        .await;

    println!("Done!");

}
