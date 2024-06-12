import time
import os

import adidasThread as Th

if __name__ == "__main__":
    if not os.path.exists("reviews/"):
        os.mkdir("reviews")
    if not os.path.exists("products/"):
        os.mkdir("products")
    threads = []
    pages_thread = Th.AdidasThread(
        t_id=1,
        t_type=Th.TYPES.PAGE,
        t_url="https://www.adidas.at/api/plp/content-engine/search?",
        t_page=0,
        t_review_obj={}
    )
    pages_thread.start()
    pages_thread.join()
    pages = Th.AdidasThread.pages
    print(len(pages))
    adThread = Th.AdidasThread(t_id=2, t_type=Th.TYPES.NONE, t_url="", t_page=0, t_review_obj={})

    thread_id = 3
    while True:
        if pages:
            page = pages.pop()
            print(page)
            products_thread = Th.AdidasThread(
                t_id=thread_id,
                t_type=Th.TYPES.PRODUCT,
                t_url="https://www.adidas.at/api/plp/content-engine/search?",
                t_page=page,
                t_review_obj={}
            )
            products_thread.start()
            threads.append(products_thread)
            thread_id += 1
            time.sleep(.5)
        if products := adThread.products:
            product = products.pop()
            review_obj = {"product_id": product["productId"], "model_id": product["modelId"]}
            review_thread = Th.AdidasThread(
                t_id=thread_id,
                t_type=Th.TYPES.REVIEW,
                t_url="",
                t_page=0,
                t_review_obj=review_obj
            )
            review_thread.start()
            threads.append(review_thread)
            thread_id += 1
            time.sleep(.5)
        else:
            if adThread.unsuccessful_links:
                print("retrying for unsuccessful links")
                obj = adThread.unsuccessful_links.pop()
                retry_thread = Th.AdidasThread(
                    t_id=thread_id,
                    t_type=obj["t_type"],
                    t_url=obj["t_url"],
                    t_page=obj["t_page"],
                    t_review_obj=obj["t_review_obj"]
                )
                retry_thread.start()
                threads.append(retry_thread)
                thread_id += 1
                time.sleep(.5)
                continue
            for thread in threads:
                thread.join()
            if products:
                continue
            print("DONE")
            break
