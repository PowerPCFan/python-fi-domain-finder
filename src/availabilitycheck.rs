use std::{collections::HashMap, fs::File};
use reqwest;

pub async fn check_domain_available(client: &reqwest::Client, domain: &str) {
    println!("Checking domain {}", domain);
    let mut form_data = HashMap::new();
    // form_data.insert("token", TOKEN); might be used for rate limiting, I didn't see a difference as of July 19th 2025
    form_data.insert("domain", domain);
    form_data.insert("domains[]", domain);

     // This url seems to have a very good ratelimiting policy
     // If you use another service, you might need to modify form_data
    let res = client.post("https://www.domainhotelli.fi/asiakkaat/modules/addons/ispapidomaincheck/domain_search_wrapper_cnic.php")
        .form(&form_data)
        .send()
        .await;

    let response = res.unwrap();

    if response.status() != 200 {
        println!("Service returned {}", response.status());
    }

    let text = response.text().await.unwrap();
    if text.contains("available") {
        println!("!!! Found available domain: {} !!!", domain)
    }
}