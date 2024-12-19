import dns.resolver
import concurrent.futures

MAX_THREADS = 500

def get_spf_domains(domain):
    spf_domains = []

    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for answer in answers:
            txt_record = answer.to_text()
            if 'v=spf' in txt_record.lower():
                spf_parts = txt_record.split(' ')
                for part in spf_parts:
                    if part.startswith('include:'):
                        included_domain = part.split(':')[1]
                        spf_domains.append(included_domain)

    except dns.resolver.NXDOMAIN:
        print(f"No such domain: {domain}")
    except dns.resolver.NoAnswer:
        print(f"No TXT record found for {domain}")

    return spf_domains

def flatten_spf_domains(domain, flattened_domains=None):
    if flattened_domains is None:
        flattened_domains = set()

    spf_domains = get_spf_domains(domain)

    for included_domain in spf_domains:
        flattened_domains.add(included_domain)
        flatten_spf_domains(included_domain, flattened_domains)

    return flattened_domains

def process_domain(domain):
    flattened_domains = flatten_spf_domains(domain)
    if flattened_domains:
        result = f"{domain}: {', '.join(flattened_domains)}"
    else:
        result = f"No included domains found in SPF for {domain}"
    return result

def process_domains(input_filename, output_filename):
    with open(input_filename, 'r') as input_file:
        domains = input_file.read().splitlines()

    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_domain = {executor.submit(process_domain, domain): domain for domain in domains}
        for future in concurrent.futures.as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing {domain}: {e}")

    with open(output_filename, 'w') as output_file:
        for result in results:
            output_file.write(result + '\n')

def main():
    input_filename = "domains.txt"
    output_filename = "results.txt"

    process_domains(input_filename, output_filename)
    print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    main()
