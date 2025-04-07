import argparse
import logging
import warnings

from deepsearcher.configuration import Configuration, init_config
from deepsearcher.offline_loading import load_from_local_files, load_from_website
from deepsearcher.online_query import query

httpx_logger = logging.getLogger("httpx")  # disable openai's logger output
httpx_logger.setLevel(logging.WARNING)


warnings.simplefilter(action="ignore", category=FutureWarning)  # disable warning output


def main():
    config = Configuration()  # Customize your config here
    init_config(config=config)

    parser = argparse.ArgumentParser(prog="deepsearcher", description="Deep Searcher.")
    ## Arguments of query
    parser.add_argument("--query", type=str, default="", help="query question or search topic.")
    parser.add_argument(  # TODO: Will move this init arg into config
        "--max_iter",
        type=int,
        default=3,
        help="Max iterations of reflection. Default is 3.",
    )

    ## Arguments of loading
    parser.add_argument(
        "--load",
        type=str,
        nargs="+",  # 1 or more files or urls
        help="Load knowledge from local files or from URLs.",
    )

    parser.add_argument(
        "--collection_name",
        type=str,
        default=None,
        help="Destination collection name of loaded knowledge.",
    )
    parser.add_argument(
        "--collection_desc",
        type=str,
        default=None,
        help="Description of the collection.",
    )

    parser.add_argument(
        "--force_new_collection",
        type=bool,
        default=False,
        help="If you want to drop origin collection and create a new collection on every load, set to True",
    )

    args = parser.parse_args()
    if args.query:
        query(args.query, max_iter=args.max_iter)
    else:
        if args.load:
            urls = [url for url in args.load if url.startswith("http")]
            local_files = [file for file in args.load if not file.startswith("http")]
            kwargs = {}
            if args.collection_name:
                kwargs["collection_name"] = args.collection_name
            if args.collection_desc:
                kwargs["collection_description"] = args.collection_desc
            if args.force_new_collection:
                kwargs["force_new_collection"] = args.force_new_collection
            if len(urls) > 0:
                load_from_website(urls, **kwargs)
            if len(local_files) > 0:
                load_from_local_files(local_files, **kwargs)
        else:
            print("Please provide a query or a load argument.")


if __name__ == "__main__":
    main()
