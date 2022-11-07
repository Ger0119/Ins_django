from cProfile import label
from cgitb import reset
from subprocess import call
from tkinter.messagebox import RETRY
from django.shortcuts import render,redirect
from django.views.generic import View
from datetime import date,datetime,timedelta
from django.utils.timezone import localtime
from django.conf import settings
import requests
import json
import math
import pandas as pd
from .models import Insight, Post, HashTag
from .forms import HashtagForm, AccountForm,IDForm
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
import time
from dateutil import relativedelta
# Create your views here.

def get_credentials(ID='k_ger1'):
    credentials = {}
    credentials['access_token'] = settings.ACCESS_TOKEN
    credentials['instagram_id'] = settings.INSTAGRAM_ID
    credentials['graph_domain'] = 'https://graph.facebook.com/'
    credentials['graph_version'] = 'v15.0'
    credentials['endpoint_base'] = credentials['graph_domain'] + credentials['graph_version'] + '/'
    credentials['ig_username'] = ID#'hathle'#'k_ger1'

    return credentials

def get_account_info(params):
    endpoint_params = {}
    endpoint_params['fields'] = f'business_discovery.username({params["ig_username"]})'+'{username,profile_picture_url,\
        follows_count,followers_count,media_count,\
        media.limit(10){comments_count,like_count,caption,media_url,permalink,timestamp,media_type,\
            children{media_url,media_type}}}'
    endpoint_params['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_id']

    return call_api(url,endpoint_params)

def call_api(url, endpoint_params=''):
    if endpoint_params:
        data = requests.get(url,params=endpoint_params)
    else:
        data = requests.get(url)
    response = {}
    response['json_data'] = json.loads(data.content)
    return response

def get_media_insights(params):
    endpoint_params = {}
    endpoint_params['metric'] = 'engagement,impressions,reach,saved'
    endpoint_params['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['media_id'] + '/insights'

    return call_api(url,endpoint_params)

class IndexView(View):
    def get(self,request,*args,**kwargs):
        form = IDForm(request.POST or None)
        Post.objects.all().delete()
        return render(request,'account_id.html',{
            'form' : form
        })
    def post(self,request,*args,**kwargs):
        form = IDForm(request.POST or None)
        if not form.is_valid():
            return redirect('index')
        ID = form.cleaned_data['ID']
        params = get_credentials(ID)

        account_response = get_account_info(params)
        # print(account_response)
        if 'error' in account_response['json_data']:
            return render(request,'index.html',{'error': 'Error : Invalid ID'})

        business_discovery = account_response['json_data']['business_discovery']
        # print(business_discovery)
        account_data = {
            'profile_picture_url': business_discovery['profile_picture_url'],
            'username': business_discovery['username'],
            'followers_count':business_discovery['followers_count'],
            'follows_count':business_discovery['follows_count'],
            'media_count' : business_discovery['media_count'],
        }
        today = date.today()

        obj, created = Insight.objects.update_or_create(
            label = today,
            defaults={
                'follower': business_discovery['followers_count'],
                'follows': business_discovery['follows_count']
            }
        )

        media_insight_data = Insight.objects.all().order_by('label')
        follower_data = []
        follows_data = []
        ff_data = []
        label_data = []
        for data in media_insight_data:
            follower_data.append(data.follower)
            follows_data.append(data.follows)
            try:
                ff = math.floor((data.follower/data.follows) * 100) / 100
            except ZeroDivisionError:
                ff = 0
            ff_data.append(ff)
            label_data.append(data.label)

        Insight_data = {
            'follower_data': follower_data,
            'follows_data':follows_data,
            'ff_data' :ff_data,
            'label_data':label_data,
        }

        like = 0
        comment = 0
        count = 1
        post_timestamp = ''

        for data in business_discovery['media']['data']:
            timestamp = localtime(datetime.strptime(data['timestamp'],'%Y-%m-%dT%H:%M:%S%z')).strftime('%Y-%m-%d')

            if post_timestamp == timestamp:
                like += data['like_count']
                comment += data['comments_count']
                count += 1
            else:
                like = data['like_count']
                comment = data['comments_count']
                post_timestamp = timestamp

            obj, created = Post.objects.update_or_create(
                label = timestamp,
                defaults={
                    'like' : like,
                    'comment':comment,
                    'count':count,
                }
            )

        post_data = Post.objects.all().order_by('label')
        like_data = []
        comment_data = []
        count_data = []
        post_label_data = []
        for data in post_data:
            like_data.append(data.like)
            comment_data.append(data.comment)
            count_data.append(data.count)
            post_label_data.append(data.label)
        Post_data = {
            'like_data':like_data,
            'comment_data':comment_data,
            'count_data':count_data,
            'post_label_data':post_label_data,
        }

        latest_media_data = business_discovery['media']['data'][0]
        params['media_id'] = latest_media_data['id']
        media_response = get_media_insights(params)
        engagement= 0
        impression= 0
        reach= 0
        save = 0
        if 'data' in media_response['json_data']:
            media_data = media_response['json_data']['data']
            engagement= media_data[0]['values'][0]['value']
            impression= media_data[1]['values'][0]['value']
            reach= media_data[2]['values'][0]['value']
            save=media_data[3]['values'][0]['value']
        if latest_media_data['media_type'] == 'CAROUSEL_ALBUM':
            media_url = latest_media_data['children']['data'][0]['media_url']
            if latest_media_data['children']['data'][0]['media_url'] == 'VIDEO':
                media_type = 'VIDEO'
            else:
                media_type = 'IMAGE'
        else:
            media_url = latest_media_data['media_url']
            media_type = latest_media_data['media_type']

        insight_media_data = {
            'caption': latest_media_data['caption'],
            'media_type': media_type,
            'media_url': media_url,
            'permalink': latest_media_data['permalink'],
            'timestamp': localtime(datetime.strptime(latest_media_data['timestamp'], '%Y-%m-%dT%H:%M:%S%z')).strftime('%Y/%m/%d %H:%M'),
            'like_count': latest_media_data['like_count'],
            'comments_count': latest_media_data['comments_count'],
            'engagement': engagement,
            'impression':impression,
            'reach': reach,
            'save': save,
        }

        return render(request,'index.html',{
            'today':today.strftime('%Y-%m-%d'),
            'account_data' : account_data,
            'Insight_data':json.dumps(Insight_data),
            'Post_data':json.dumps(Post_data),
            'insight_media_data':insight_media_data,
        })


def get_hashtag_id(params):
    endpoint_params = {}

    endpoint_params['user_id'] = params['instagram_id']
    endpoint_params['q'] = params['hashtag_name']
    endpoint_params['fields'] = 'id,name'
    endpoint_params['access_token'] = params['access_token']
    url = params['endpoint_base'] + 'ig_hashtag_search'
    return call_api(url,endpoint_params)

def get_hashtag_media(params):
    endpoint_params = {}
    endpoint_params['user_id'] = params['instagram_id']
    endpoint_params['fields'] = 'id,media_type,media_url,permalink,like_count,comments_count,caption,timestamp,children{id,media_url}'
    endpoint_params['limit'] = 50
    endpoint_params['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['hashtag_id'] + '/recent_media'

    return call_api(url,endpoint_params)


class HashtagView(View):
    def get_media_list(self,hashtag_id_response,hashtag_media_list):

        for item in hashtag_id_response['json_data']['data']:
            if item.get('media_type') == 'CAROUSEL_ALBUM':
                media_url = item['children']['data'][0]['media_url']
                # print(item['children']['data'])
                if item['children']['data'][0].get('media_type') == 'VIDEO':
                    media_type = 'VIDEO'
                else: 
                    media_type = 'IMAGE'
            else:
                try:
                    media_url = item['media_url']
                except KeyError:
                    media_url = 'http://placehold.jp/500x500.png?text=None'

                media_type = item.get('media_type')
                if not media_type:
                    continue

                   
            timestamp = localtime(datetime.strptime(item['timestamp'],'%Y-%m-%dT%H:%M:%S%z')).strftime('%Y-%m-%d')

            hashtag_media_list.append([
                media_type,
                media_url,
                item['permalink'],
                item.get('like_count',0),
                item['comments_count'],
                timestamp,
            ])
        return hashtag_media_list

    def get(self,request,*args,**kwargs):
        form = HashtagForm(request.POST or None)

        return render(request,'search.html',{
            'form' : form
        })

    def post(self,request,*args,**kwargs):
        form = HashtagForm(request.POST or None)

        if form.is_valid():
            hashtag = form.cleaned_data['hashtag']

            params = get_credentials()
            params['hashtag_name'] = hashtag

            hashtag_id_response = get_hashtag_id(params)

            params['hashtag_id'] = hashtag_id_response['json_data']['data'][0]['id']

            hashtag_media_response = get_hashtag_media(params)
            
            hashtag_media_list = []

            hashtag_media_list = self.get_media_list(hashtag_media_response,hashtag_media_list)

            while True:
                if not hashtag_media_response['json_data'].get('paging'):
                    break
                
                next_url = hashtag_media_response['json_data']['paging']['next']
                hashtag_data = hashtag_media_response['json_data']['data']
                if hashtag_data and next_url:
                    hashtag_media_response = call_api(next_url)

                    hashtag_media_list = self.get_media_list(hashtag_id_response,hashtag_media_list)
                
                else:
                    break
            hashtag_media_data = pd.DataFrame(hashtag_media_list,columns=[
                'media_type',
                'media_url',
                'permalink',
                'like_count',
                'comments_count',
                'timestamp'
            ])
            hashtag_media_data = hashtag_media_data.sort_values(['like_count','comments_count'],ascending=[False,False])

            post_counts = hashtag_media_data['timestamp'].value_counts().to_dict()

            for key, value in post_counts.items():

                obj, created = HashTag.objects.update_or_create(
                    label=key,
                    tag=hashtag,
                    defaults={
                        'count':value
                    }
                )
            
            hashtag_data = HashTag.objects.filter(tag=hashtag).order_by('label')
            count_data = []
            label_data = []
            for data in hashtag_data:
                count_data.append(data.count)
                label_data.append(data.label)
            
            hashtag_count_data = {
                'count_data': count_data,
                'label_data':label_data,
            }
            return render(request,'hashtag.html',{
                'hashtag_media_data':hashtag_media_data,
                'hashtag':hashtag,
                'hashtag_count_data':json.dumps(hashtag_count_data)
            })
        else:
            redirect('hashtag')


def search_account(url, keyword):
    options = Options()
    options.add_argument('--headless')  # バックグランドで実行
    options.add_argument('--no-sandbox')  # chrootで隔離された環境(Sandbox)での動作を無効
    options.add_argument('--disable-dev-shm-usage') # 共有メモリファイルの場所を/dev/shmから/tmpに移動
    options.add_argument('--disable-gpu')
    options.add_experimental_option('excludeSwitches',['enable-automation','enable-logging'])

    driver = webdriver.Chrome(executable_path=r'D:\Data\Python\BellTech_Learning\14_Instagram\chromedriver.exe', options=options)
    driver.get(url)

    input_element = driver.find_element(By.ID,'gsc-i-id1')
    input_element.clear()
    input_element.send_keys(keyword)
    input_element.send_keys(Keys.RETURN)
    time.sleep(2)

    return driver

def get_user_id(driver):
    '''
    ページからページネーションしながらURLを取得し、user_idを1つのリストにまとめる
    '''
    i = 2
    urls = []
    user_ids = []

    while True:
        # urlを収集
        url_objects = driver.find_elements(By.CSS_SELECTOR,'div.gsc-thumbnail-inside > div > a')
        # もしurlのリストが存在するなら
        if url_objects:
            for object in url_objects:
                urls.append(object.get_attribute('href'))
        # urlのリストが存在しない場合->ページが終わった可能性あり
        else:
            print('URLが取得できませんでした。')
        try:
            urls.remove(None)
        except:
            pass

        # ページ送りを試す
        try:
            driver.find_element(By.XPATH,f"//div[@id='___gcse_1']/div/div/div/div[5]/div[2]/div/div/div[2]/div/div[{i}]").click()
            print('次のページに行きます。')
            time.sleep(1)
        except:
            print('ページがなくなりました')
            break
        i += 1
        # アカウントのurlリストからuser_idの部分を取得　m.group(1)
    for text in urls:
        match = re.search(r'https://www.instagram.com/(.*?)/', text)
        if match:
            user_id = match.group(1)
            user_ids.append(user_id)
    user_ids = list(set(user_ids))

    return user_ids

def get_pagenate_account_info(params):
    # print(params)
    endpoint_params = {}
    if type(params['after_key']) == list:
        if len(params['after_key']) > 0:
            params['after_key'] = params['after_key'].pop()
        else:
            params['after_key']  = ''
    
    endpoint_params['fields'] = 'business_discovery.username(' + params['ig_username'] + '){media.after(' + params['after_key'] + ').limit(1000){timestamp}}'
    endpoint_params['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_account_id']
    return call_api(url, endpoint_params)

class AccountView(View):

    def get(self,request,*args,**kwargs):
        form = AccountForm(request.POST or None,
            initial={
                'post_count':1000,
                'followers_count':1000,
                'created_at':'0',
                'year':1,
            }
        )


        return render(request,'account_search.html',{
            'form' : form
        })
    def post(self,request,*args,**kwargs):
        form = AccountForm(request.POST or None)

        if form.is_valid():
            keyword = form.cleaned_data['keyword']
            post_count = form.cleaned_data['post_count']
            followers_count = form.cleaned_data['followers_count']
            created_at = form.cleaned_data['created_at']
            year = int(form.cleaned_data['year'])
            
            url = 'https://makitani.net/igusersearch/'
            driver = search_account(url, keyword)
            
            user_ids = get_user_id(driver)
            with open('user_id.txt','w') as f:
                for user in user_ids:
                    f.write(user)
                    f.write('\n')

            # Instagram Graph API認証情報取得
            params = get_credentials()

            user_list = []

            for user_id in user_ids:
                params['ig_username'] = user_id

                try:
                    # アカウント情報取得
                    account_response = get_account_info(params)
                    business_discovery = account_response['json_data']['business_discovery']

                    if business_discovery['media_count'] <= post_count and business_discovery['followers_count'] >= followers_count:
                        if created_at:
                            user_list.append([
                                user_id,
                                business_discovery.get('profile_picture_url'),
                                business_discovery.get('followers_count',0),
                                business_discovery.get('follows_count',0),
                                business_discovery.get('media_count',0),
                                'https://www.instagram.com/' + user_id
                            ])
                        else:
                            try:
                                after_key = business_discovery['media']['paging']['cursors']['after']
                            except KeyError:
                                after_key = ''
                            params['after_key'] = after_key
                            pagenate_account_response = get_pagenate_account_info(params)
                            # 最初に投稿された日を取得
                            timestamp = pagenate_account_response['json_data']['business_discovery']['media']['data'][-1]['timestamp']
                            m = re.search('((\d{4})-\d{2}-\d{2}).*', timestamp)
                            # アカウント開設日を取得
                            created = (datetime.strptime(m.group(1), '%Y-%m-%d')).date()
                            # 〇年前を取得
                            last_year = date.today() - relativedelta.relativedelta(years=year)

                            # 1年以内に開設したアカウントかを判定
                            # if created >= last_year:
                            #     user_list.append([
                            #         user_id,
                            #         business_discovery['profile_picture_url'],
                            #         business_discovery['followers_count'],
                            #         business_discovery['follows_count'],
                            #         business_discovery['media_count'],
                            #         'https://www.instagram.com/' + user_id
                            #     ])

                except KeyError:
                    pass

            user_data = pd.DataFrame(user_list, columns=[
                'username',
                'profile_picture_url',
                'followers_count',
                'follows_count',
                'media_count',
                'link'
            ])
            return render(request, 'keyword.html', {
                'user_data': user_data,
                'keyword': keyword,
                'media_count': post_count,
                'followers_count': followers_count,
                'created_at': created_at,
                'year': year,
            })
        else:      
            return redirect('account')

