import json
import boto3
import datetime
import uuid

from django.views import View
from django.http import JsonResponse
from django.core.cache import cache
from django.db         import IntegrityError
from django.db.models import Count, Q, F

from .models import Product, Post, Comment, ProductLike, Cheered, Watched
from user.models import User
from my_settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from user.utils  import user_validator

POST_LIMIT   = 8
REVIEW_LIMIT = 2
TOP_TEN      = 10

class DetailView(View):
    @user_validator
    def get(self,request, product_id):
        try:
            user_id=request.user.id
            product      = Product.objects.select_related(
                'category', 
                'sub_category', 
                'creator', 
                'level', 
                'coupon'
                ).prefetch_related(
                    'image_set',
                    'tags', 
                    'review_set', 
                    'post_set',
                    'post_set__user',
                    'post_set__comment_set',
                    'post_set__comment_set__user',
                    'review_set__user',
                    'productlike_set', 
                    'introduction_set', 
                    'basicinfo_set',
                    'titlecover_set',
                    ).get(id=product_id)
            if not Watched.objects.filter(product_id=product_id, user_id=user_id).exists():
                Watched.objects.create(product_id=product_id, user_id=user_id)
                
            if product.is_open:
                data={
                    'product_id'   : product.id,
                    'header_images':[
                        {
                            "src": image.image_url
                        } for image in product.image_set.all()],

                    'detail_aside':{
                        'category'    : product.sub_category.name,
                        'creator_name': product.creator.nickname,
                        'title'       : product.name,
                        'price'       : product.price,
                        'discount'    : product.discount,
                        'liked'       : product.productlike_set.filter(user_id=user_id).exists(),
                        'heart'       : product.productlike_set.count()
                    },

                    'detail':{
                        'class_info':{
                            'chapter'     : product.chapter,
                            'sub_chapter' : product.chapter_detail,
                            'is_subtitled': product.subtitle_flag,
                            'level'       : product.level.name,
                            'class_detail': product.basicinfo_set.first().category_detail,
                            'to_learn'    : [
                                {'description': product.introduction_set.first().theme_description,
                                'image_url'  : product.introduction_set.first().theme_image_url},
                                {'description': product.introduction_set.first().process_description,
                                'image_url'  : product.introduction_set.first().process_image_url},
                                {'description': product.introduction_set.first().work_description,
                                'image_url'  : product.introduction_set.first().work_image_url}
                                ]
                            }
                        },
                    
                    'reviews':{
                        'review_length': product.review_set.all().count(),
                        'satis'        : product.review_set.filter(good_bad=True).count()/product.review_set.all().count()*100 if product.review_set.all().count()!=0 else 0,
                        'content':[
                            {
                                'description':post.content
                            } for post in product.post_set.all()[:POST_LIMIT]],
                        'comment_list':[{
                            'profile_image': review.user.image_url,
                            'nickname'     : review.user.name,
                            'date'         : review.created_at,
                            'description'  : review.content
                        } for review in product.review_set.all()[:REVIEW_LIMIT]]
                    },

                    'notice':[
                        {
                            'profile_image': product.creator.image_url,
                            'nickname'     : product.creator.nickname,
                            'date'         : post.created_at,
                            'description'  : post.content
                        }
                    for post in product.post_set.filter(user_id__creator_id=product.creator_id)],

                    'community':[
                        {   
                            'post_id'      : post.id,
                            'profile_image': post.user.image_url,
                            'nickname'     : post.user.name,
                            'date'         : post.created_at,
                            'description'  : post.content,
                            'comments': [{
                                'comment_id'       : comment.id,
                                'profile_image'    : comment.user.image_url,
                                'nickname'         : comment.user.name,
                                'date'             : comment.created_at,
                                'description'      : comment.content,
                                'comment_image_url': comment.image_url
                            } for comment in post.comment_set.all()]
                        }
                    for post in product.post_set.all() if post.user_id!=User.objects.get(creator_id=product.creator_id).id]
                    }
                return JsonResponse(data, status=200)

            data={
                'product_id'     : product.id,
                'title'          : product.titlecover_set.first().title,
                'mentor'         : product.creator.nickname,
                'category'       : product.basicinfo_set.first().category.name,
                'sub_category'   : product.basicinfo_set.first().sub_category.name,
                'category_detail': product.basicinfo_set.first().category_detail,
                'level'          : product.basicinfo_set.first().level.name,
                'cover_image'    : product.titlecover_set.first().cover_image_url,
                'thumbnail_image': product.titlecover_set.first().thumbnail_image_url,
                'liked'          : product.productlike_set.filter(user_id=user_id).exists(),
                'like_count'     : product.productlike_set.count(),
                'cheered'        : product.cheered_set.filter(user_id=user_id).exists(),
                'cheer_count'    : product.cheered_set.count()
            }
            
            return JsonResponse(data, status=200)
            
        except Product.DoesNotExist:
            return JsonResponse({'message':'PRODUCT_DOES_NOT_EXIST'}, status=400)

class CommentView(View):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    @user_validator
    def post(self, request, product_id, post_id):
        try:
            user_id=request.user.id
            content=request.POST['content']
            
            if request.FILES.get('file'):
                file=request.FILES['file']
                filename=str(uuid.uuid1()).replace('-','')
                
                self.s3_client.upload_fileobj(
                    file,
                    "class-dev101",
                    filename,
                    ExtraArgs={
                        "ContentType": file.content_type
                    }
                )
                file_url=f"https://s3.ap-northeast-2.amazonaws.com/class-dev101/{filename}"
            else:
                file_url=None

            new_comment=Comment.objects.create(
                post_id=post_id,
                user_id=user_id,
                content=content,
                image_url=file_url
            )
            data={
                'post_id':new_comment.post.id,
                'comment_id':new_comment.id,
                'user':new_comment.user.name,
                'user_image_url':new_comment.user.image_url,
                'created_at':new_comment.created_at,
                'content':new_comment.content,
                'comment_image_url':new_comment.image_url
            }
            
            return JsonResponse(data, status=200)

        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)
        except IntegrityError:
            return JsonResponse({'message':'POST_DOES_NOT_EXIST'}, status=400)

class ProductsView(View):
    def get(self, request):
        OFFSET     = int(request.GET.get('offset'))
        LIMIT      = int(request.GET.get('limit'))
        filter_set = {}
        if request.GET.get('category'):
            filter_set['category__name'] = request.GET['category']
            cache.delete('products')

        if not cache.get('products'):
            products         = Product.objects.select_related(
                'sub_category', 
                'creator', 
                ).prefetch_related(
                    'image_set',
                    'productlike_set',
                    'titlecover_set',
                    'cheered_set', 
                    'review_set').all()
            
            top_products     = products.annotate(count=Count('productlike__product_id')).filter(is_open=True, **filter_set).order_by('-count')
            planned_products = products.filter(is_open=False, **filter_set)
            updated_products = products.filter(is_open=True, **filter_set).order_by('-updated_at')

            if OFFSET >= len(updated_products):
                return JsonResponse({'message':'PAGE_NOT_FOUND'}, status=404)
            updated_products=updated_products[OFFSET:OFFSET+LIMIT]

            data={
                'top_10_data':[
                    {
                        'product_id'  : product.id,
                        'image_url'   : product.image_set.first().image_url,
                        'sub_category': product.sub_category.name,
                        'mentor'      : product.creator.nickname,
                        'title'       : product.name,
                        'like_count'  : product.productlike_set.all().count(),
                        'thumbs_up'   : product.review_set.filter(good_bad=True).count()/product.review_set.all().count(),
                        'price'       : product.price,
                        'discount'    : product.discount,
                        'coupon'      : product.coupon.name
                    }
                if product.review_set.all().count()!=0 else {
                        'product_id'  : product.id,
                        'image_url'   : product.image_set.first().image_url,
                        'sub_category': product.sub_category.name,
                        'mentor'      : product.creator.nickname,
                        'title'       : product.name,
                        'like_count'  : product.productlike_set.all().count(),
                        'thumbs_up'   : 0,
                        'price'       : product.price,
                        'discount'    : product.discount,
                        'coupon'      : product.coupon.name
                    } for product in top_products[:TOP_TEN]],

                'planned_data':[
                    {
                        'product_id'  : product.id,
                        'image_url'   : product.titlecover_set.first().thumbnail_image_url,
                        'is_open'     : product.is_open,
                        'sub_category': product.sub_category.name,
                        'mentor'      : product.creator.nickname,
                        'title'       : product.titlecover_set.first().title,
                        'like_count'  : product.productlike_set.all().count(),
                        'cheered'     : product.cheered_set.count(),
                    } for product in planned_products if product.titlecover_set.exists()],

                'updated_data':[
                    {
                        'product_id'  : product.id,
                        'image_url'   : product.image_set.first().image_url,
                        'sub_category': product.sub_category.name,
                        'mentor'      : product.creator.nickname,
                        'title'       : product.name,
                        'like_count'  : product.productlike_set.all().count(),
                        'thumbs_up'   : product.review_set.filter(good_bad=True).count()/product.review_set.all().count(),
                        'coupon'      : product.coupon.name,
                        'updated_at'  : product.updated_at
                    }
                if product.review_set.all().count()!=0 else {
                        'product_id'  : product.id,
                        'image_url'   : product.image_set.first().image_url,
                        'sub_category': product.sub_category.name,
                        'mentor'      : product.creator.nickname,
                        'title'       : product.name,
                        'like_count'  : product.productlike_set.all().count(),
                        'thumbs_up'   : 0,
                        'coupon'      : product.coupon.name,
                        'updated_at'  : product.updated_at
                    } for product in updated_products]
                }
            data=cache.set('products', data)
        data=cache.get('products')
        return JsonResponse(data, status=200)

class SearchView(View):
    def get(self, request):
        try:
            OFFSET     = int(request.GET.get('offset'))
            LIMIT      = int(request.GET.get('limit'))
            products   = Product.objects.select_related(
                'category',
                'sub_category',
                'coupon',
                'creator'
                ).prefetch_related(
                    'review_set', 
                    'productlike_set',
                    'image_set'
                    ).filter(is_open=True)
            filter_set = {}
            query      = Q()
            sortings   = {
                'updated'     : '-created_at',
                'satisfaction': products.filter(Q(review__good_bad=True)|Q(review__good_bad=None)).annotate(count=Count('review__good_bad')).order_by('-count'),
                'popular'     : products.annotate(count=Count('productlike__product_id')).order_by('-count')
            }
            search  = request.GET.get('query')
            sorting = request.GET.get('sort')

            if search:
                query &= Q(name__contains=search) | Q(sub_category__name__contains=search) | Q(basicinfo__category_detail__contains=search)

            if request.GET.get('category'):
                filter_set['sub_category__name']=request.GET['category']

            if sorting:
                if sorting=='updated':
                    products = products.order_by(sortings[sorting])
                else:
                    products = sortings[sorting]

            products = products.filter(query, **filter_set)
            
            if OFFSET >= len(products):
                return JsonResponse({'message':'PAGE_NOT_FOUND'}, status=404)
            products=products[OFFSET:OFFSET+LIMIT]

            data = {
                'data':[
                {
                    'product_id'  : product.id,
                    'image_url'   : product.image_set.first().image_url,
                    'sub_category': product.sub_category.name,
                    'mentor'      : product.creator.nickname,
                    'title'       : product.name,
                    'like_count'  : product.productlike_set.all().count(),
                    'thumbs_up'   : product.review_set.filter(good_bad=True).count()/product.review_set.all().count(),
                    'price'       : product.price,
                    'discount'    : product.discount,
                    'coupon'      : product.coupon.name
                } if product.review_set.all().count()!=0 else {
                    'product_id'  : product.id,
                    'image_url'   : product.image_set.first().image_url,
                    'sub_category': product.sub_category.name,
                    'mentor'      : product.creator.nickname,
                    'title'       : product.name,
                    'like_count'  : product.productlike_set.all().count(),
                    'thumbs_up'   : 0,
                    'price'       : product.price,
                    'discount'    : product.discount,
                    'coupon'      : product.coupon.name
                    } for product in products]}
            
            return JsonResponse(data, status=200)

        except KeyError:
            return JsonResponse({'message':'WRONG_SORTING'}, status=400)
   
class ProductLikeView(View):
    @user_validator
    def post(self, request, product_id):
        try:
            user_id=request.user.id
            product=Product.objects.prefetch_related('productlike_set').get(id=product_id)
            if product.productlike_set.filter(user_id=user_id).exists():
                product.productlike_set.get(user_id=user_id).delete()
                cache.delete('products')
            else:
                ProductLike.objects.create(user_id=user_id, product_id=product_id)
                cache.delete('products')
                
            like_count=ProductLike.objects.filter(product_id=product_id).count()
            liked=ProductLike.objects.filter(product_id=product_id, user_id=user_id).exists()
            return JsonResponse({
                'liked':liked,
                'like_count':like_count}, status=200)

        except Product.DoesNotExist:
            return JsonResponse({'message':'NO_PRODUCT'}, status=400)
            
class PackageView(View):
    @user_validator
    def get(self, request, product_id):
        try:
            user_id = request.user.id
            product = Product.objects.select_related(
                'creator', 
                'level', 
                'coupon'
                ).get(id=product_id)
            
            data={
                'product_id'   : product.id,
                'package':{
                    'creator'  : product.creator.nickname,
                    'price'    : product.price,
                    'discount' : product.discount,
                    'discounted_price':int(product.price*(1-product.discount))
                }
            }
            
            return JsonResponse(data, status=200)
            
        except Product.DoesNotExist:
            return JsonResponse({'message':'PRODUCT DOES NOT EXIST'}, status=400)

class CheerView(View):
    @user_validator
    def post(self, request, product_id):
        user_id      = request.user.id
        if Product.objects.get(id=product_id).is_open:
            return JsonResponse({'message':'OPENED_CLASS'},status=400)
        if User.objects.get(id=user_id).cheer_point==0:
            return JsonResponse({'message':'CHEER_POINTS_0'}, status=403)

        obj, created = Cheered.objects.get_or_create(product_id=product_id, user_id=user_id, defaults={'product_id':product_id, 'user_id':user_id})

        if created:
            cheer_count=Cheered.objects.filter(product_id=product_id).count()
            User.objects.filter(id=user_id).update(cheer_point=F('cheer_point')-1)
            return JsonResponse({'cheer_count':cheer_count}, status=200)
        return JsonResponse({'message':'ALREADY_CHEERED'}, status=400)

        
