import cdsapi

def main():
    client = cdsapi.Client()

    dataset = ""
    request = {

            }
    target = ""
    client.retrieve(dataset, request, target)

if __name__ == "__main__":
    main()
