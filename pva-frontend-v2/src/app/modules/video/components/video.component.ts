import { Component, OnInit } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Product } from 'app/models/product';
import { VideoFacade } from '../video.facade';
import { Observable } from 'rxjs';
import { Base } from 'app/models/base';
import { Config } from 'app/models/config';
import { OfferType } from 'app/models/offertype';
import { Video } from 'app/models/video';
import { TitleCasePipe } from '@angular/common';

@Component({
  selector: 'app-video',
  templateUrl: '../views/video.component.html',
  styleUrls: ['../views/video.component.scss'],
  providers: [VideoFacade]
})
export class VideoComponent implements OnInit {

  drive_url = 'https://drive.google.com/uc?export=download&id='
  
  // Data to view
  bases : Observable<Base[]>
  products : Observable<Product[]>
  offer_types : Observable<OfferType[]>
  videos : Observable<Video[]>

  product_groups : Map<string, Product[]>
  selected_groups : Set<string> = new Set<string>()
  mode : string
  
  // Chosen
  base : Base
  configs : Array<any>
  product_keys: Array<any>
  
  constructor(private facade : VideoFacade, private _snackBar: MatSnackBar) {
      this.offer_types = this.facade.offer_types$
      this.videos = this.facade.videos
    }
    
    ngOnInit() {
      this.bases = this.facade.bases
      this.products = this.facade.products
    }
    
    choose_base(base : Base) {
      this.configs = new Array(base.products.length)
      this.product_keys = new Array(base.products.length)

      this.base = base
    }

    select_single_video_mode() {
      this.mode = 'single'
    }

    select_bulk_video_mode() {
      this.product_groups = this.facade.get_available_groups_for_base()
      this.mode = 'bulk'
    }

    is_all_filled() {
      return !this.configs.includes(undefined) && !this.product_keys.includes(undefined)
    }
    
    add_video() {
      this.facade.add_preview_video(this.configs, this.base, this.product_keys).then(response => {
        this.mode = ''
        this._snackBar.open('Saved ' + response['status'], 'OK', { duration: 2000 })
      })
    }

    check_group(element, group) {
      if (element.checked)
        this.selected_groups.add(group)
      else
        this.selected_groups.delete(group)
    }

    create_bulk() {

      for(let group of this.selected_groups) {

        const sorted_products = this.product_groups.get(group).sort((a, b) => a.position - b.position)

        this.product_keys = sorted_products.map(p => p.id)
        this.configs = sorted_products.map(p => this.facade.get_configs_from_offer_type(p.offer_type, this.base.title))

        //console.log(JSON.stringify(this.product_keys))
        //console.log(JSON.stringify(this.configs))

        this.add_video()
      }

      this._snackBar.open('Created ' + this.selected_groups.size + ' videos!', 'OK', { duration: 4000 })
    }

    update_video() {
      this.facade.update_videos()
    }

    delete_video(video : Video) {
      this.facade.delete_video(video.generated_video)
    }
    
    indexTracker(index: number, value: any) {
      return index;
    }
  }
