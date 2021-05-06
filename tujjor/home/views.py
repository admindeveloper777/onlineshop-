from django.shortcuts import render
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Avg,Count,Q,F
from django.db.models.functions import Concat
from django.http import HttpResponseRedirect,HttpResponse,JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import translation
from django.urls import reverse
from home.forms import SearchForm #shu kutibhonani tanimadi sorash kerak
from home.models import *
from tujjor import settings
from product.models import *
from user.models import UserProfile


def index(request):
    if not request.session.has_key('currency'):
        request.session['currency']=settings.DEFAULT_CURRENCY

    setting=Setting.objects.get(pk=1)
    product_latest=Product.objects.all().order_by('-id')[:4]
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=settings.LANGUAGE_CODE[0:2]

    if defaultlang != currentlang:
        setting=SettingLang.objects.get(lang=currentlang)
        products_latest=Product.objects.raw(
            'SELECT p.id,p.price,l.title,l.description,l.slug'
            'FROM product_product as p'
            'LEFT JOIN product_productlang as l'
            'ON p.id=l.product_id'
            'WHERE l.lang=%s ORDER BY p.id DESC LIMIT 4',[currentlang]
            )
        products_slider=Product.objects.all().order_by('id')[:4]
        products_picked=Product.objects.all().order_by('?')[:4]
        post=Post.objects.all().order_by('-id')[:4]
        page="home"
        context={
            'setting':setting,
            'page':page,
            'products_slider':products_slider,
            'products_picked':products_picked,
            'products_latest':products_latest,

        }
    return render(request,'index.html',context)

def selectlanguage(request):
    if request.method=='POST':
        cur_language=translation.get_language()
        lastur1=request.META.get('HTTP_REFERER')
        lang=request.POST['language']
        translation.activate(lang)
        request.session[translation.LANGUAGE_SESSION_KEY]=lang
        return HttpResponseRedirect('/'+lang)
def aboutus(request):
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=request.LANGUAGE_CODE[0:2]
    setting=Setting.objects.get(pk=1)
    if defaultlang != currentlang:
        setting=SettingLang.objects.get(lang=currentlang)

    context={'setting':setting}
    return render(request,'about.html',context)
def contactus(request):
    currentlang=request.LANGUAGE_CODE[0:2]
    if request.method=='POST':
        form=ContactForm(request.POST)
        if form.is_valid():
            data=ContactMessage()
            data.name=form.cleaned_data['name']
            data.email=form.cleaned_data['email']
            data.subject=form.cleaned_data['subject']
            data.message=form.cleaned_data['message']
            data.ip=request.META.get['REMOTE_ADDR']
            data.save()
            messages.succcess(request,"Your Message has been sent.Thank you for your message")
            return HttpResponseRedirect('/contact')
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=request.LANGUAGE_CODE[0:2]
    setting=Setting.objects.get(pk=1)
    if defaultlang != currentlang:
        setting=SettingLang.objects.get(lang=currentlang)

    form=ContactForm()
    context={'setting':setting,'form':form}
    return render(request,'contact.html',context)

def category_products(request,id,slug):
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=request.LANGUAGE_CODE[0:2]
    catdata=Category.objects.get(pk=id)
    products=Product.objects.filter(category_id=id)
    if defaultlang != currentlang:
        try:
            products=Product.objects.raw(
                'SELECT p.id,p.price,p.amount,p.image,p.variant,l.title,l.keywords,l.description,l.slug,l.detail'
                'FROM product_product as p'
                'LEFT JOIN product_productlang as l'
                'ON p.id=l.product_id'
                'WHERE p.category_id=%s and l.lang=%s',[id,currentlang]
                )

        except:
            pass
        catdata=CategoryLang.objects.get(category_id=id,lang=currentlang)
    context={
        'products':products,
        'catdata':catdata ,   }
    return render(request,'category_products.html',context )
def search(request):
    if request.method=='POST':
        form=SearchForm(request.POST)
        if form.is_valid():
            query=form.cleaned_data['query']
            catid=form.cleaned_data['catid']
            if catid==0:
                products=Product.objects.filter(title_icontains=query)
            else:
                products=Product.objects.filter(title_icontains=query)
            category=Category.objects.all()
            context={'products':products,'query':query}
            return render(request,'search_products.html',context)
        return HttpResponseRedirect('/')
def search_auto(request):
    if request.is_ajax():
        q=request.GET.get('term','')
        products=Product.objects.filter(title_icontains=q) #shu joyida hatolik bolishi mumkin
        results=[]
        for rs in products:
            product_json={}
            product_json=rs.title+">"+rs.category.title
            results.append(product_json)
        data=json.dumps(results)
    else:
        data='fail'
    mimetype='application/json'
    return HttpResponse(data,mimetype)
def product_detail(request,id,slug):
    query=request.GET.get('q')
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=request.LANGUAGE_CODE[0:2]
    category=Category.objects.all()
    product=Product.objects.get(pk=id)
    if defaultlang != currentlang:
        try:
            prolang = Product.objects.raw(
                'SELECT p.id,p.price,p.image,p.amount,p.variant,l.title,l.description,l.keywords,l.slug,l.detail'
                'FROM product_product as p'
                'INNER JOIN product_productlang as l'
                'ON p.id=l.product_id'
                'WHERE p.id=$s and l.lang=%s', [id, currentlang]

            )
            product = prolang[0]
        except:
            pass
    images=Images.objects.filter(product_id=id)
    comments=Comment.objects.filter(product_id=id,status=True)
    context={
        'product':product,'category':category,
        'images':images,'comments':comments, }
    if product.variant !="None":
        if request.method == 'POST':
            variant_id=request.POST.get['variantid']
            variant=Variants.objects.get(id=variant_id)
            colors=Variants.objects.filter(product_id=id,size_id=variant.size_id)
            sizes=Variants.objects.raw('SELECT *FROM product_variants WHERE product_id=%s GROUP BY size_id',[id])
            query +=variant.title + 'Size: '+str(variant.size)+'Color: '+str(variant.color)
        else:
            variants=Variants.objects.filter(product_id=id)
            colors=Variants.objects.filter(product_id=id,size_id=variants[0].size_id)
            sizes=Variants.objects.raw('SELEC *FROM product_variants WHERE product_id=%s GROUP BY size_id',[id])
            variant=Variants.objects.get(id=variants[0].id)
        context.update({'sizes':sizes,'colors':colors,'variant':variant,'query':query})
    return render(request,'product_detail.html',context)

def post_detail(request,id,slug):# postga ozgartirib ketdiim
    query=request.GET.get('q')
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=request.LANGUAGE_CODE[0:2]
    post=Post.objects.get(pk=id)
    if defaultlang != currentlang:
        try:
            prolang=Post.objects.raw(
                'SELECT p.id,p.image,l.title,l.keywords,l.description,l.slug,l.detail'
                'FROM post_post as p'
                'INNER JOIN post_postlang as l'
                'ON p.id=l.post_id'
                'WHERE p.id=%s, and l.lang=%s',[id,currentlang]
            )
            post=prolang[0]
        except:
            pass
    images=Images.objects.filter(post_id=id)
    context={'post':post,'images':images,}
    return render(request,'post_detail.html',context)
def ajaxcolor(request):
    data={}
    if request.POST.get('action')=='post':
        size_id=request.POST.get('size')
        productid=request.POSt.get('productid')
        colors=Variants.objects.filter(product_id=productid,size_id=size_id)
        context={'size_id':size_id,
                 'productid':productid,
                 'colors':colors,}
        data={'rendered_table':render_to_string('color_list.html',context=context)}
        return JsonResponse(data)
    return JsonResponse(data)

def licence_detail(request,id,slug):
    query=request.GET.get('q')
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=request.LANGUAGE_CODE[0:2]

    licence=License.objects.get(pk=1)
    if defaultlang !=currentlang:
        try:
            liclang=License.objects.raw(
                'SELECT lc.id,lc.image,l.title,l.keywords,l.description,l.slug,l.detail'
                'FROM licence_licence as lc'
                'INNER JOIN licence_licencelang as l'
                'ON lc.id=licence_id'
                'WHERE lc.id=%s and l.lang=%s',[id,currentlang]
            )
            licence=liclang[0]
        except:
            pass
    images=LicenseImages.objects.filter(licence_id=id)
    context={
        'licence':licence,
        'images':images,
    }
    return render(request,'lic_detail.html',context)

def faq(request):
    defaultlang=settings.LANGUAGE_CODE[0:2]
    currentlang=request.LANGUAGE_CODE[0:2]
    if defaultlang ==currentlang:
        faq=FAQ.objects.filter(status='True',lang=defaultlang).order_by('ordernumber')
    else:
        faq=FAQ.objects.filter(status='True',lang=currentlang).order_by('ordernumber')
    context={'faq':faq}

    return render(request,'faq.html',context)

def selectcurrency(request):
    lasturl=request.META.get('HTTP_REFERER')
    if request.method=='POST':
        request.session['currency']=request.POST['currency']
    return HttpResponseRedirect(lasturl)
@login_required(login_url='/login')
def savelangcur(request):
    lasturl=request.META.get('HTTP_REFERER')
    curren_user=request.user
    language=Language.objects.get(code=request.LANGUAGE_CODE[0:2])
    data=UserProfile.objects.get(user_id=curren_user.id)
    data.language_id=language.id
    data.currency_id=request.session['currency']
    data.save()
    return HttpResponseRedirect(lasturl)

