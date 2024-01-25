import argparse
import os

from news_based.news_crawler import crawl_news
from news_based.news_openai_static import generate_email as static_email
from news_based.news_openai import generate_email as dynamic_email
from generator import main as generate_email_main
from pipeline import pipeline

def main():
    parser = argparse.ArgumentParser(description="Your program description")
    subparsers = parser.add_subparsers(title='subcommands', dest='command')
    pipeline_parser = subparsers.add_parser('pipeline', help='Pipeline command help')
    news_based_parser = subparsers.add_parser('news-based', help='News-based command help')
    news_based_parser.add_argument('style', choices=['static', 'dynamic'], help='Style of Email')
    news_based_parser.add_argument('language', help='Language of Email')
    generate_parser = subparsers.add_parser('generate', help='Generate command help')
    generate_parser.add_argument('input_file_url', help='Input HTML file Path')
    generate_parser.add_argument('output_file_url', help='Output HTML file Path')

    args = parser.parse_args()

    if args.command == 'pipeline':
        pipeline()
    elif args.command == 'news-based':
        if not os.path.exists("news.json"):
            crawl_news()
        
        if args.style == "static":
            static_email(open_in_browser=True, language=args.language)
        else:
            dynamic_email(open_in_browser=True, language=args.language)
    elif args.command == 'generate':
        generate_email_main(args.input_file_url, args.output_file_url)

if __name__ == "__main__":
    main()
