use std::{fs::File, io::Read};

pub fn load_words(path: &str) -> Vec<String> {
    let mut file = File::open(path).expect("Failed to open file");
    let mut contents = String::new();

    file.read_to_string(&mut contents).expect("Failed to read file");

    return contents.split("\n").map(|line| line.to_string()).collect()
}

pub fn find_n_letter_words(words: Vec<String>, length: usize) -> Vec<String> {
    if length == 0 {
        return words;
    }
    return words.into_iter().filter(|line| line.len() == length).collect();
}
    